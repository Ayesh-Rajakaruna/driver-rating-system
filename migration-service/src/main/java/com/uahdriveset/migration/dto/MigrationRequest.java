package com.uahdriveset.migration.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Request body for POST /api/v1/migration/start.
 * datasetPath must point to the extracted UAH-DriveSet root folder
 * (the folder that directly contains D1, D2, D3... driver sub-folders).
 * If omitted, migration.default-dataset-path from application.yml is used.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class MigrationRequest {
    private String datasetPath;
}
