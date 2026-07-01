package com.uahdriveset.migration.controller;

import com.uahdriveset.migration.dto.MigrationRequest;
import com.uahdriveset.migration.dto.MigrationResponse;
import com.uahdriveset.migration.service.MigrationService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/migration")
@RequiredArgsConstructor
public class MigrationController {

    private final MigrationService migrationService;

    @org.springframework.beans.factory.annotation.Value("${migration.default-dataset-path}")
    private String defaultDatasetPath;

    /**
     * Single API call that migrates the entire UAH-DriveSet dataset into MySQL.
     * POST /api/v1/migration/start
     * Body (optional): { "datasetPath": "/absolute/path/to/UAH-DRIVESET-v1" }
     * If datasetPath is omitted, migration.default-dataset-path from application.yml is used.
     *
     * The run is idempotent: trips already present (matched by folder name) are skipped,
     * so re-calling this endpoint after adding new trip folders only imports the new ones.
     */
    @PostMapping("/start")
    public ResponseEntity<MigrationResponse> startMigration(
            @RequestBody(required = false) MigrationRequest request) {
        String datasetPath = (request != null && request.getDatasetPath() != null && !request.getDatasetPath().isBlank())
                ? request.getDatasetPath()
                : defaultDatasetPath;

        MigrationResponse response = migrationService.migrate(datasetPath);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("UAH-DriveSet migration service is up");
    }
}
