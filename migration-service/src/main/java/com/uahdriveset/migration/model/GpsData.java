package com.uahdriveset.migration.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "gps_data", indexes = @Index(name = "idx_gps_trip_time", columnList = "trip_id,timestamp_sec"))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GpsData {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "gps_id")
    private Long gpsId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false)
    private Trip trip;

    // Seconds elapsed since trip start, as recorded in RAW_GPS.txt (not wall-clock time).
    @Column(name = "timestamp_sec", precision = 12, scale = 3)
    private BigDecimal timestampSec;

    @Column(name = "speed_kmh", precision = 8, scale = 3)
    private BigDecimal speedKmh;

    @Column(name = "latitude", precision = 10, scale = 7)
    private BigDecimal latitude;

    @Column(name = "longitude", precision = 10, scale = 7)
    private BigDecimal longitude;

    @Column(name = "altitude", precision = 8, scale = 2)
    private BigDecimal altitude;

    @Column(name = "vertical_accuracy", precision = 8, scale = 3)
    private BigDecimal verticalAccuracy;

    @Column(name = "horizontal_accuracy", precision = 8, scale = 3)
    private BigDecimal horizontalAccuracy;

    @Column(name = "course", precision = 8, scale = 3)
    private BigDecimal course;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}
