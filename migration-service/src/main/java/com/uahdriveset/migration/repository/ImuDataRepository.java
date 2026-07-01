package com.uahdriveset.migration.repository;

import com.uahdriveset.migration.model.ImuData;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ImuDataRepository extends JpaRepository<ImuData, Long> {
}
