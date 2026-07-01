package com.uahdriveset.migration.repository;

import com.uahdriveset.migration.model.GpsData;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GpsDataRepository extends JpaRepository<GpsData, Long> {
}
