package com.uahdriveset.migration.model.enums;

public enum BehaviorType {
    NORMAL,
    AGGRESSIVE,
    DROWSY,
    UNKNOWN;

    public static BehaviorType fromFolderToken(String token) {
        if (token == null) {
            return UNKNOWN;
        }
        String normalized = token.trim().toUpperCase();
        if (normalized.contains("AGGRESSIVE")) {
            return AGGRESSIVE;
        }
        if (normalized.contains("DROWSY")) {
            return DROWSY;
        }
        if (normalized.contains("NORMAL")) {
            return NORMAL;
        }
        return UNKNOWN;
    }
}
