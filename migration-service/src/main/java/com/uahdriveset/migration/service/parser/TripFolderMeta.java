package com.uahdriveset.migration.service.parser;

import com.uahdriveset.migration.model.enums.BehaviorType;
import com.uahdriveset.migration.model.enums.RoadType;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;

/**
 * UAH-DriveSet trip folders follow the pattern:
 *   {yyyyMMddHHmmss}-{distance}km-{driverCode}-{BEHAVIOR}-{ROAD_TYPE}
 * e.g. "20151111135612-16km-D1-NORMAL-MOTORWAY"
 * Any folder that doesn't match this pattern is skipped by the migration service.
 */
public record TripFolderMeta(
        String folderName,
        LocalDateTime startTime,
        Double distanceKm,
        String driverCode,
        BehaviorType behaviorType,
        RoadType roadType
) {

    private static final DateTimeFormatter TS_FORMAT = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

    public static TripFolderMeta parse(String folderName) {
        String[] parts = folderName.split("-");
        if (parts.length < 5) {
            return null;
        }
        try {
            LocalDateTime startTime = LocalDateTime.parse(parts[0], TS_FORMAT);
            String distanceToken = parts[1].toLowerCase().replace("km", "").trim();
            Double distanceKm = distanceToken.isBlank() ? null : Double.parseDouble(distanceToken);
            String driverCode = parts[2];
            BehaviorType behaviorType = BehaviorType.fromFolderToken(parts[3]);
            RoadType roadType = RoadType.fromFolderToken(parts[4]);
            return new TripFolderMeta(folderName, startTime, distanceKm, driverCode, behaviorType, roadType);
        } catch (DateTimeParseException | NumberFormatException e) {
            return null;
        }
    }
}
