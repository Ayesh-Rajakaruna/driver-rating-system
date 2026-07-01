package com.uahdriveset.migration.service.parser;

import com.uahdriveset.migration.model.RoadSegmentReading;
import com.uahdriveset.migration.model.Trip;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;

import static com.uahdriveset.migration.service.parser.RawTextFileReader.col;

/**
 * Parses SEMANTIC_ONLINE.txt (the OSM-derived road-type / speed-limit lookups).
 * Column layout (0-indexed), per the UAH-DriveSet documentation:
 *   0 timestamp (s)   1 osm road type token   2 max legal speed (km/h)
 * NOTE: verify these offsets against the README shipped with your copy of the dataset -
 * this file's layout varies more between dataset releases than RAW_GPS/RAW_ACCELEROMETERS.
 */
@Component
@RequiredArgsConstructor
public class SemanticOnlineParser {

    private static final String FILE_NAME = "SEMANTIC_ONLINE.txt";

    private final RawTextFileReader reader;

    public List<RoadSegmentReading> parse(Path tripFolder, Trip trip) throws IOException {
        return reader.readLines(tripFolder.resolve(FILE_NAME), columns -> {
            if (columns.length < 2) {
                return null;
            }
            Integer speedLimit = null;
            if (columns.length > 2) {
                var speedDecimal = col(columns, 2);
                speedLimit = speedDecimal == null ? null : speedDecimal.intValue();
            }
            return RoadSegmentReading.builder()
                    .trip(trip)
                    .timestampSec(col(columns, 0))
                    .osmRoadType(RawTextFileReader.colStr(columns, 1))
                    .speedLimitKmh(speedLimit)
                    .build();
        });
    }
}
