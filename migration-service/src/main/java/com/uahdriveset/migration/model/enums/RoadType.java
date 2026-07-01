package com.uahdriveset.migration.model.enums;

public enum RoadType {
    MOTORWAY,
    SECONDARY,
    UNKNOWN;

    public static RoadType fromFolderToken(String token) {
        if (token == null) {
            return UNKNOWN;
        }
        String normalized = token.trim().toUpperCase();
        if (normalized.contains("MOTORWAY")) {
            return MOTORWAY;
        }
        if (normalized.contains("SECONDARY")) {
            return SECONDARY;
        }
        return UNKNOWN;
    }
}
