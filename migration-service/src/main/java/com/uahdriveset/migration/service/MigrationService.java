package com.uahdriveset.migration.service;

import com.uahdriveset.migration.dto.MigrationResponse;
import com.uahdriveset.migration.exception.MigrationException;
import com.uahdriveset.migration.model.*;
import com.uahdriveset.migration.repository.*;
import com.uahdriveset.migration.service.parser.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

/**
 * Orchestrates a full migration run: walks {datasetPath}/D*/{trip-folder}/*.txt,
 * upserts drivers/trips, and bulk-inserts the time-series tables.
 * Each trip is imported in its own transaction so one malformed trip folder
 * doesn't roll back the whole run.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MigrationService {

    private final DriverRepository driverRepository;
    private final TripRepository tripRepository;
    private final GpsDataRepository gpsDataRepository;
    private final ImuDataRepository imuDataRepository;
    private final RoadSegmentReadingRepository roadSegmentReadingRepository;
    private final EventRepository eventRepository;
    private final TripLabelRepository tripLabelRepository;

    private final GpsFileParser gpsFileParser;
    private final ImuFileParser imuFileParser;
    private final SemanticOnlineParser semanticOnlineParser;
    private final EventFileParser eventFileParser;

    public MigrationResponse migrate(String datasetPath) {
        Instant start = Instant.now();
        Path root = Path.of(datasetPath);
        if (!Files.isDirectory(root)) {
            throw new MigrationException("Dataset path does not exist or is not a directory: " + datasetPath);
        }

        List<String> skippedTrips = new ArrayList<>();

        int driversCreated = 0;
        int tripsProcessed = 0;
        long gpsRows = 0;
        long imuRows = 0;
        long roadRows = 0;
        long eventRows = 0;
        int labelsInserted = 0;

        List<Path> tripFolders = findTripFolders(root);
        log.info("Discovered {} candidate trip folders under {}", tripFolders.size(), datasetPath);

        for (Path tripFolder : tripFolders) {
            String folderName = tripFolder.getFileName().toString();
            TripFolderMeta meta = TripFolderMeta.parse(folderName);
            if (meta == null) {
                log.warn("Skipping folder with unrecognized name pattern: {}", folderName);
                skippedTrips.add(folderName + " (unrecognized folder name pattern)");
                continue;
            }
            try {
                TripImportResult result = importSingleTrip(tripFolder, meta);
                if (result.driverCreated()) {
                    driversCreated++;
                }
                tripsProcessed++;
                gpsRows += result.gpsRows();
                imuRows += result.imuRows();
                roadRows += result.roadRows();
                eventRows += result.eventRows();
                labelsInserted += result.labelInserted() ? 1 : 0;
            } catch (Exception e) {
                log.error("Failed to import trip folder {}: {}", folderName, e.getMessage(), e);
                skippedTrips.add(folderName + " (" + e.getMessage() + ")");
            }
        }

        Duration elapsed = Duration.between(start, Instant.now());
        log.info("Migration finished in {}s - trips={}, gpsRows={}, imuRows={}, roadRows={}, eventRows={}",
                elapsed.toSeconds(), tripsProcessed, gpsRows, imuRows, roadRows, eventRows);

        return MigrationResponse.builder()
                .status(skippedTrips.isEmpty() ? "SUCCESS" : "COMPLETED_WITH_SKIPS")
                .driversCreated(driversCreated)
                .tripsProcessed(tripsProcessed)
                .gpsRowsInserted(gpsRows)
                .imuRowsInserted(imuRows)
                .roadSegmentRowsInserted(roadRows)
                .eventRowsInserted(eventRows)
                .tripLabelsInserted(labelsInserted)
                .skippedTrips(skippedTrips)
                .elapsedTime(elapsed)
                .build();
    }

    /**
     * Each trip folder is imported in its own REQUIRES_NEW transaction so a parse failure
     * in one trip does not affect previously committed trips or abort the whole batch.
     */
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public TripImportResult importSingleTrip(Path tripFolder, TripFolderMeta meta) throws IOException {
        String folderName = meta.folderName();

        Optional<Trip> existing = tripRepository.findByFolderName(folderName);
        if (existing.isPresent()) {
            log.info("Trip {} already imported, skipping (idempotent re-run)", folderName);
            return TripImportResult.empty();
        }

        boolean driverCreated = false;
        Driver driver = driverRepository.findByDriverCode(meta.driverCode()).orElse(null);
        if (driver == null) {
            driver = driverRepository.save(Driver.builder().driverCode(meta.driverCode()).build());
            driverCreated = true;
        }

        Trip trip = tripRepository.save(Trip.builder()
                .driver(driver)
                .folderName(folderName)
                .startTime(meta.startTime())
                .distanceKm(meta.distanceKm() == null ? null : java.math.BigDecimal.valueOf(meta.distanceKm()))
                .roadType(meta.roadType())
                .behaviorType(meta.behaviorType())
                .build());

        List<GpsData> gpsRows = gpsFileParser.parse(tripFolder, trip);
        gpsDataRepository.saveAll(gpsRows);

        List<ImuData> imuRows = imuFileParser.parse(tripFolder, trip);
        imuDataRepository.saveAll(imuRows);

        List<RoadSegmentReading> roadRows = semanticOnlineParser.parse(tripFolder, trip);
        roadSegmentReadingRepository.saveAll(roadRows);

        List<Event> eventRows = eventFileParser.parse(tripFolder, trip);
        eventRepository.saveAll(eventRows);

        tripLabelRepository.save(TripLabel.builder()
                .trip(trip)
                .drivingBehavior(meta.behaviorType())
                .notes("Derived from trip folder name at import time")
                .build());

        log.info("Imported trip {} (driver={}, gps={}, imu={}, road={}, events={})",
                folderName, meta.driverCode(), gpsRows.size(), imuRows.size(), roadRows.size(), eventRows.size());

        return new TripImportResult(driverCreated, gpsRows.size(), imuRows.size(), roadRows.size(), eventRows.size(), true);
    }

    /**
     * Trip folders sit two levels below the dataset root: {root}/{driverFolder}/{tripFolder}/*.txt
     */
    private List<Path> findTripFolders(Path root) {
        List<Path> result = new ArrayList<>();
        try (Stream<Path> driverDirs = Files.list(root)) {
            for (Path driverDir : driverDirs.filter(Files::isDirectory).toList()) {
                try (Stream<Path> tripDirs = Files.list(driverDir)) {
                    tripDirs.filter(Files::isDirectory).forEach(result::add);
                } catch (IOException e) {
                    log.warn("Could not list driver folder {}: {}", driverDir, e.getMessage());
                }
            }
        } catch (IOException e) {
            throw new MigrationException("Could not list dataset root: " + root, e);
        }
        return result;
    }

    private record TripImportResult(boolean driverCreated, long gpsRows, long imuRows, long roadRows,
                                     long eventRows, boolean labelInserted) {
        static TripImportResult empty() {
            return new TripImportResult(false, 0, 0, 0, 0, false);
        }
    }
}
