package com.uahdriveset.migration.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * One row per SEMANTIC_ONLINE.txt reading. Kept denormalized (trip_id + timestamp) rather than
 * deduped into a master road_segments + junction table, since the raw file emits one OSM lookup
 * per GPS timestamp rather than a stable set of reusable segments.
 */
@Entity
@Table(name = "road_segment_readings", indexes = @Index(name = "idx_road_trip_time", columnList = "trip_id,timestamp_sec"))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RoadSegmentReading {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "reading_id")
    private Long readingId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false)
    private Trip trip;

    @Column(name = "timestamp_sec", precision = 12, scale = 3)
    private BigDecimal timestampSec;

    @Column(name = "osm_road_type", length = 30)
    private String osmRoadType;

    @Column(name = "speed_limit_kmh")
    private Integer speedLimitKmh;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}
