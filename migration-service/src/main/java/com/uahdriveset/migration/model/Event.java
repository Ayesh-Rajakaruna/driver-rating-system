package com.uahdriveset.migration.model;

import com.uahdriveset.migration.model.enums.EventType;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "events", indexes = @Index(name = "idx_events_trip_time", columnList = "trip_id,timestamp_sec"))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Event {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "event_id")
    private Long eventId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false)
    private Trip trip;

    @Column(name = "timestamp_sec", precision = 12, scale = 3)
    private BigDecimal timestampSec;

    @Enumerated(EnumType.STRING)
    @Column(name = "event_type", length = 20)
    private EventType eventType;

    @Column(name = "description", length = 255)
    private String description;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    public void prePersist() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}
