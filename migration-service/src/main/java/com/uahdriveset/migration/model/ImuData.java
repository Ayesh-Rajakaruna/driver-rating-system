package com.uahdriveset.migration.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "imu_data", indexes = @Index(name = "idx_imu_trip_time", columnList = "trip_id,timestamp_sec"))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ImuData {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "imu_id")
    private Long imuId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false)
    private Trip trip;

    @Column(name = "timestamp_sec", precision = 12, scale = 3)
    private BigDecimal timestampSec;

    @Column(name = "acc_x_raw", precision = 10, scale = 5)
    private BigDecimal accXRaw;

    @Column(name = "acc_y_raw", precision = 10, scale = 5)
    private BigDecimal accYRaw;

    @Column(name = "acc_z_raw", precision = 10, scale = 5)
    private BigDecimal accZRaw;

    @Column(name = "acc_x_kf", precision = 10, scale = 5)
    private BigDecimal accXKf;

    @Column(name = "acc_y_kf", precision = 10, scale = 5)
    private BigDecimal accYKf;

    @Column(name = "acc_z_kf", precision = 10, scale = 5)
    private BigDecimal accZKf;

    @Column(name = "roll", precision = 10, scale = 5)
    private BigDecimal roll;

    @Column(name = "pitch", precision = 10, scale = 5)
    private BigDecimal pitch;

    @Column(name = "yaw", precision = 10, scale = 5)
    private BigDecimal yaw;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}
