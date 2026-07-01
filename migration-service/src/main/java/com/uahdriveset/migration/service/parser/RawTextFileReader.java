package com.uahdriveset.migration.service.parser;

import org.springframework.stereotype.Component;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

/**
 * UAH-DriveSet RAW_*.txt / SEMANTIC_*.txt files are plain text, one record per line,
 * columns separated by one or more spaces. This reader turns each non-blank line
 * into a String[] of columns and hands it to a per-file mapper.
 */
@Component
public class RawTextFileReader {

    public <T> List<T> readLines(Path filePath, Function<String[], T> mapper) throws IOException {
        List<T> results = new ArrayList<>();
        if (!Files.exists(filePath)) {
            return results;
        }
        List<String> lines = Files.readAllLines(filePath);
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.isEmpty()) {
                continue;
            }
            String[] columns = trimmed.split("\\s+");
            T mapped = mapper.apply(columns);
            if (mapped != null) {
                results.add(mapped);
            }
        }
        return results;
    }

    public static BigDecimal col(String[] columns, int index) {
        if (index < 0 || index >= columns.length) {
            return null;
        }
        try {
            return new BigDecimal(columns[index]);
        } catch (NumberFormatException e) {
            return null;
        }
    }

    public static String colStr(String[] columns, int index) {
        return (index >= 0 && index < columns.length) ? columns[index] : null;
    }
}
