package com.uahdriveset.migration.service.parser;

import com.uahdriveset.migration.model.Event;
import com.uahdriveset.migration.model.Trip;
import com.uahdriveset.migration.model.enums.EventType;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import static com.uahdriveset.migration.service.parser.RawTextFileReader.col;

/**
 * Parses EVENTS_LIST_LANE_CHANGES.txt into LANE_CHANGE events.
 * Column layout (0-indexed): 0 timestamp (s), remaining columns are event-specific
 * metadata that is folded into the free-text description column.
 * NOTE: verify offsets against the README shipped with your copy of the dataset.
 */
@Component
@RequiredArgsConstructor
public class EventFileParser {

    private static final String FILE_NAME = "EVENTS_LIST_LANE_CHANGES.txt";

    private final RawTextFileReader reader;

    public List<Event> parse(Path tripFolder, Trip trip) throws IOException {
        Path filePath = tripFolder.resolve(FILE_NAME);
        if (!Files.exists(filePath)) {
            return new ArrayList<>();
        }
        return reader.readLines(filePath, columns -> {
            if (columns.length < 1) {
                return null;
            }
            return Event.builder()
                    .trip(trip)
                    .timestampSec(col(columns, 0))
                    .eventType(EventType.LANE_CHANGE)
                    .description(String.join(" ", columns))
                    .build();
        });
    }
}
