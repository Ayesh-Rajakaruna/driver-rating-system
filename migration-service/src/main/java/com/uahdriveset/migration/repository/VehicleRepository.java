package com.uahdriveset.migration.repository;

import com.uahdriveset.migration.model.Vehicle;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface VehicleRepository extends JpaRepository<Vehicle, Integer> {
    Optional<Vehicle> findByVehicleCode(String vehicleCode);
}
