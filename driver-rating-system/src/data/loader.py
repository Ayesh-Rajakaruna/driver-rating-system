"""
Data loading for the UAH-DriveSet.

Handles the multi-file-per-trip layout of the dataset and falls back
to a synthetic generator when the real dataset is not present.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

from config.settings import AppConfig, BehaviorLabel, RoadType, DataConfig

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Value object: one raw trip
# ─────────────────────────────────────────────

class TripData:
    """
    Container for all raw sensor streams of a single UAH-DriveSet trip.

    Attributes:
        trip_id:   Unique identifier (folder name).
        behavior:  Ground-truth driving behaviour label.
        road_type: Motorway or Secondary road.
        gps:       DataFrame with GPS readings (1 Hz).
        accel:     DataFrame with accelerometer readings (10 Hz).
        gyro:      DataFrame with gyroscope readings (10 Hz).
    """

    __slots__ = ("trip_id", "behavior", "road_type", "gps", "accel", "gyro")

    def __init__(
        self,
        trip_id:   str,
        behavior:  BehaviorLabel,
        road_type: RoadType,
        gps:       pd.DataFrame,
        accel:     pd.DataFrame,
        gyro:      pd.DataFrame,
    ) -> None:
        self.trip_id   = trip_id
        self.behavior  = behavior
        self.road_type = road_type
        self.gps       = gps
        self.accel     = accel
        self.gyro      = gyro

    def __repr__(self) -> str:
        return (
            f"TripData(id={self.trip_id!r}, "
            f"behavior={self.behavior.name}, "
            f"road={self.road_type.value}, "
            f"gps_rows={len(self.gps)}, "
            f"accel_rows={len(self.accel)})"
        )


# ─────────────────────────────────────────────
#  UAH-DriveSet loader
# ─────────────────────────────────────────────

class UAHDataLoader:
    """
    Loads raw CSV files from a UAH-DriveSet directory tree.

    UAH folder name format::

        Date(YYYYMMDDhhmmss)-Distance(Km)-D<n>-<Behavior>-<Road>
        e.g. 20151130132506-1.2Km-D1-Normal-Motorway

    Each folder contains::

        RAW_GPS.txt          (1 Hz)
        RAW_ACCELEROMETERS.txt (10 Hz)
        RAW_GYROSCOPES.txt   (10 Hz)
        PROC_SEMANTICS.txt   (labels)

    Args:
        config: Application configuration object.
    """

    _FOLDER_PATTERN = re.compile(
        r"\d{14}-[\d.]+Km-D\d+-(?P<behavior>\w+)-(?P<road>\w+)",
        re.IGNORECASE,
    )

    def __init__(self, config: AppConfig) -> None:
        self._cfg   = config.data
        self._root  = Path(config.data.dataset_root)

    # ── public interface ───────────────────────

    def load_all(self) -> list[TripData]:
        """
        Discover and load every trip folder under ``dataset_root``.

        Returns:
            List of :class:`TripData` objects (one per trip).

        Raises:
            FileNotFoundError: If ``dataset_root`` does not exist.
        """
        if not self._root.exists():
            raise FileNotFoundError(
                f"Dataset root not found: {self._root}. "
                "Download UAH-DriveSet or use SyntheticDataGenerator."
            )

        trips: list[TripData] = []
        for folder in sorted(self._root.rglob("*")):
            if folder.is_dir() and self._FOLDER_PATTERN.match(folder.name):
                try:
                    trip = self._load_trip(folder)
                    trips.append(trip)
                    logger.debug("Loaded %s", trip)
                except Exception as exc:          # noqa: BLE001
                    logger.warning("Skipping %s — %s", folder.name, exc)

        logger.info("Loaded %d trips from %s", len(trips), self._root)
        return trips

    # ── private helpers ────────────────────────

    def _load_trip(self, folder: Path) -> TripData:
        match = self._FOLDER_PATTERN.match(folder.name)
        behavior  = self._parse_behavior(match.group("behavior"))
        road_type = self._parse_road(match.group("road"))

        gps   = self._read_csv(folder / "RAW_GPS.txt",           self._cfg.gps_columns)
        accel = self._read_csv(folder / "RAW_ACCELEROMETERS.txt", self._cfg.accel_columns)
        gyro  = self._read_csv(folder / "RAW_GYROSCOPES.txt",    self._cfg.gyro_columns)

        return TripData(
            trip_id=folder.name,
            behavior=behavior,
            road_type=road_type,
            gps=gps,
            accel=accel,
            gyro=gyro,
        )

    @staticmethod
    def _read_csv(path: Path, columns: tuple) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        df = pd.read_csv(
            path,
            sep=r"\s+",
            header=None,
            names=list(columns),
            comment="#",
        )
        df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
        return df.dropna(subset=["timestamp"]).reset_index(drop=True)

    @staticmethod
    def _parse_behavior(raw: str) -> BehaviorLabel:
        mapping = {
            "normal":     BehaviorLabel.NORMAL,
            "drowsy":     BehaviorLabel.DROWSY,
            "aggressive": BehaviorLabel.AGGRESSIVE,
        }
        return mapping.get(raw.lower(), BehaviorLabel.NORMAL)

    @staticmethod
    def _parse_road(raw: str) -> RoadType:
        return (
            RoadType.MOTORWAY
            if raw.lower() in ("motorway", "highway")
            else RoadType.SECONDARY
        )


# ─────────────────────────────────────────────
#  Synthetic data generator (fallback / testing)
# ─────────────────────────────────────────────

class SyntheticDataGenerator:
    """
    Generates realistic synthetic driving data for development and testing.

    Produces trips with statistically distinct IMU/GPS profiles per
    :class:`BehaviorLabel`, mimicking the UAH-DriveSet distributions.

    Args:
        config:     Application configuration object.
        n_trips:    Number of synthetic trips to generate.
        seed:       NumPy random seed for reproducibility.
    """

    # Behaviour → (accel_mean, accel_std, gyro_std, speed_mean)
    _PROFILES: dict[BehaviorLabel, tuple[float, float, float, float]] = {
        BehaviorLabel.NORMAL:     (0.5,  0.8, 0.05, 25.0),
        BehaviorLabel.DROWSY:     (0.3,  0.6, 0.03, 20.0),
        BehaviorLabel.AGGRESSIVE: (1.8,  2.5, 0.35, 32.0),
    }

    def __init__(
        self,
        config:  AppConfig,
        n_trips: int = 60,
        seed:    int = 42,
    ) -> None:
        self._cfg     = config.data
        self._n_trips = n_trips
        self._rng     = np.random.default_rng(seed)

    def generate(self) -> list[TripData]:
        """
        Return a list of :class:`TripData` with synthetic sensor readings.

        The data is balanced: each :class:`BehaviorLabel` gets
        ``n_trips // 3`` trips (plus leftover assigned to NORMAL).
        """
        labels    = list(BehaviorLabel)
        trips_per = self._n_trips // len(labels)
        trips: list[TripData] = []

        for i, label in enumerate(labels):
            count = trips_per if i < len(labels) - 1 else (
                self._n_trips - trips_per * (len(labels) - 1)
            )
            for j in range(count):
                road = RoadType.MOTORWAY if j % 2 == 0 else RoadType.SECONDARY
                trips.append(self._make_trip(label, road, idx=len(trips)))

        logger.info("Generated %d synthetic trips.", len(trips))
        return trips

    def _make_trip(
        self,
        label:    BehaviorLabel,
        road:     RoadType,
        idx:      int,
        duration: int = 300,      # seconds
    ) -> TripData:
        accel_mean, accel_std, gyro_std, speed_mean = self._PROFILES[label]
        t_gps   = np.arange(duration)                  # 1 Hz
        t_imu   = np.arange(0, duration, 0.1)          # 10 Hz

        # GPS
        speed = np.clip(
            self._rng.normal(speed_mean, 3.0, size=len(t_gps)), 0, 45
        )
        lat = 40.0 + np.cumsum(self._rng.normal(0, 0.0001, len(t_gps)))
        lon = -3.0 + np.cumsum(self._rng.normal(0, 0.0001, len(t_gps)))
        gps = pd.DataFrame({
            "timestamp": t_gps,
            "speed_ms":  speed,
            "lat":       lat,
            "lon":       lon,
            "altitude":  self._rng.uniform(600, 700, len(t_gps)),
            "vertical_accuracy":   0.5,
            "horizontal_accuracy": 1.0,
        })

        # Accelerometers
        ax = self._rng.normal(0,          accel_std,  len(t_imu))
        ay = self._rng.normal(0,          accel_std * 0.6, len(t_imu))
        az = self._rng.normal(accel_mean, accel_std,  len(t_imu))
        accel = pd.DataFrame({"timestamp": t_imu, "ax": ax, "ay": ay, "az": az})

        # Gyroscopes
        gx = self._rng.normal(0, gyro_std, len(t_imu))
        gy = self._rng.normal(0, gyro_std, len(t_imu))
        gz = self._rng.normal(0, gyro_std, len(t_imu))
        gyro = pd.DataFrame({"timestamp": t_imu, "gx": gx, "gy": gy, "gz": gz})

        return TripData(
            trip_id=f"synthetic-{idx:04d}",
            behavior=label,
            road_type=road,
            gps=gps,
            accel=accel,
            gyro=gyro,
        )
