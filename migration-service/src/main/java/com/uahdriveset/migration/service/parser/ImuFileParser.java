package com.uahdriveset.migration.service.parser;

import com.uahdriveset.migration.model.ImuData;
import com.uahdriveset.migration.model.Trip;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;

import static com.uahdriveset.migration.service.parser.RawTextFileReader.col;

/**
 * Parses RAW_ACCELEROMETERS.txt.
 * Column layout (0-indexed), per the UAH-DriveSet documentation:
 *   0 timestamp (s)     1 car-stopped flag (ignored here)
 *   2 acc X raw   3 acc Y raw   4 acc Z raw
 *   5 acc X (Kalman filtered)   6 acc Y (KF)   7 acc Z (KF)
 *   8 roll   9 pitch   10 yaw
 * NOTE: verify these offsets against the README shipped with your copy of the dataset.
 */
@Component
@RequiredArgsConstructor
public class ImuFileParser {

    private static final String FILE_NAME = "RAW_ACCELEROMETERS.txt";

    private final RawTextFileReader reader;

    public List<ImuData> parse(Path tripFolder, Trip trip) throws IOException {
        return reader.readLines(tripFolder.resolve(FILE_NAME), columns -> {
            if (columns.length < 8) {
                return null;
            }
            return ImuData.builder()
                    .trip(trip)
                    .timestampSec(col(columns, 0))
                    .accXRaw(col(columns, 2))
                    .accYRaw(col(columns, 3))
                    .accZRaw(col(columns, 4))
                    .accXKf(col(columns, 5))
                    .accYKf(col(columns, 6))
                    .accZKf(col(columns, 7))
                    .roll(col(columns, 8))
                    .pitch(col(columns, 9))
                    .yaw(col(columns, 10))
                    .build();
        });
    }
}
