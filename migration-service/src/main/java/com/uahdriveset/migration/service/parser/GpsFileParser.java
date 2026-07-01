package com.uahdriveset.migration.service.parser;

import com.uahdriveset.migration.model.GpsData;
import com.uahdriveset.migration.model.Trip;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;

import static com.uahdriveset.migration.service.parser.RawTextFileReader.col;

/**
 * Parses RAW_GPS.txt.
 * Column layout (0-indexed), per the UAH-DriveSet documentation:
 *   0 timestamp (s)   1 speed (km/h)     2 latitude (deg)   3 longitude (deg)
 *   4 altitude (m)    5 vertical accuracy (m)  6 horizontal accuracy (m)  7 course (deg)
 * NOTE: verify these offsets against the README shipped with your copy of the dataset -
 * some releases add/reorder trailing columns.
 */
@Component
@RequiredArgsConstructor
public class GpsFileParser {

    private static final String FILE_NAME = "RAW_GPS.txt";

    private final RawTextFileReader reader;

    public List<GpsData> parse(Path tripFolder, Trip trip) throws IOException {
        return reader.readLines(tripFolder.resolve(FILE_NAME), columns -> {
            if (columns.length < 4) {
                return null;
            }
            return GpsData.builder()
                    .trip(trip)
                    .timestampSec(col(columns, 0))
                    .speedKmh(col(columns, 1))
                    .latitude(col(columns, 2))
                    .longitude(col(columns, 3))
                    .altitude(col(columns, 4))
                    .verticalAccuracy(col(columns, 5))
                    .horizontalAccuracy(col(columns, 6))
                    .course(col(columns, 7))
                    .build();
        });
    }
}
