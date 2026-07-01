package com.uahdriveset.migration.repository;

import com.uahdriveset.migration.model.Trip;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface TripRepository extends JpaRepository<Trip, Integer> {
    Optional<Trip> findByFolderName(String folderName);
}
