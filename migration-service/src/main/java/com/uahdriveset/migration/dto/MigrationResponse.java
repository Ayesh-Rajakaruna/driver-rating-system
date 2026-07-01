package com.uahdriveset.migration.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MigrationResponse {
    private String status;
    private int driversCreated;
    private int tripsProcessed;
    private long gpsRowsInserted;
    private long imuRowsInserted;
    private long roadSegmentRowsInserted;
    private long eventRowsInserted;
    private int tripLabelsInserted;
    @Builder.Default
    private List<String> skippedTrips = new ArrayList<>();
    private Duration elapsedTime;
}
