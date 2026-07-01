package com.uahdriveset.migration.repository;

import com.uahdriveset.migration.model.TripLabel;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TripLabelRepository extends JpaRepository<TripLabel, Integer> {
}
