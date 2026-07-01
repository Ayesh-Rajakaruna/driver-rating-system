package com.uahdriveset.migration.model;

import com.uahdriveset.migration.model.enums.BehaviorType;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "trip_labels", uniqueConstraints = @UniqueConstraint(columnNames = "trip_id"))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TripLabel {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "label_id")
    private Integer labelId;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false, unique = true)
    private Trip trip;

    @Enumerated(EnumType.STRING)
    @Column(name = "driving_behavior", length = 20)
    private BehaviorType drivingBehavior;

    @Column(name = "overall_score", precision = 5, scale = 2)
    private BigDecimal overallScore;

    @Column(name = "notes", length = 255)
    private String notes;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}
