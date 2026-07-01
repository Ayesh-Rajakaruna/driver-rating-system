package com.uahdriveset.migration.model;

import com.uahdriveset.migration.model.enums.BehaviorType;
import com.uahdriveset.migration.model.enums.RoadType;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "trips", uniqueConstraints = @UniqueConstraint(columnNames = "folder_name"))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Trip {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "trip_id")
    private Integer tripId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "driver_id", nullable = false)
    private Driver driver;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "vehicle_id")
    private Vehicle vehicle;

    // Original UAH-DriveSet trip folder name, kept for traceability and idempotent re-imports.
    @Column(name = "folder_name", nullable = false, length = 150)
    private String folderName;

    @Column(name = "start_time")
    private LocalDateTime startTime;

    @Column(name = "distance_km", precision = 10, scale = 3)
    private BigDecimal distanceKm;

    @Enumerated(EnumType.STRING)
    @Column(name = "road_type", length = 20)
    private RoadType roadType;

    @Enumerated(EnumType.STRING)
    @Column(name = "behavior_type", length = 20)
    private BehaviorType behaviorType;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}
