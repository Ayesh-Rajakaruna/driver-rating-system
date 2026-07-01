package com.uahdriveset.migration.repository;

import com.uahdriveset.migration.model.Driver;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface DriverRepository extends JpaRepository<Driver, Integer> {
    Optional<Driver> findByDriverCode(String driverCode);
}
