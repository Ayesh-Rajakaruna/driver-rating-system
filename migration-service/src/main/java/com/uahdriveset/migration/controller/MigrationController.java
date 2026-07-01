package com.uahdriveset.migration.controller;

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

    @PostMapping("/start")
    public ResponseEntity<MigrationResponse> startMigration() {
        MigrationResponse response = migrationService.migrate();
        return ResponseEntity.ok(response);
    }
}
