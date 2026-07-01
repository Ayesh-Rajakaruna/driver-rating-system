package com.uahdriveset.migration.repository;

import com.uahdriveset.migration.model.Event;
import org.springframework.data.jpa.repository.JpaRepository;

public interface EventRepository extends JpaRepository<Event, Long> {
}
