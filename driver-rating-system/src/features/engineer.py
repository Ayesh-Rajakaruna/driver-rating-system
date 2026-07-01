"""
Feature engineering for driving behaviour analysis.

Transforms raw TripData objects into a flat feature matrix
suitable for scikit-learn estimators.

Features extracted per sliding window:
    • Statistical moments of IMU axes (mean, std, max, min, RMS)
    • Jerk (derivative of acceleration)
    • Harsh-event counts (braking, cornering, acceleration)
    • Speed statistics from GPS
    • Road-type encoding
"""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
import pandas as pd

from config.settings import AppConfig, BehaviorLabel, RoadType, ThresholdConfig
from data.loader import TripData

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Event detector
# ─────────────────────────────────────────────

class HarshEventDetector:
    """
    Detects harsh driving events from raw IMU windows.

    Args:
        config: Threshold configuration (g-force limits).
    """

    def __init__(self, config: ThresholdConfig) -> None:
        self._cfg = config

    def count_harsh_brakes(self, ax_window: np.ndarray) -> int:
        """Count samples with longitudinal deceleration > threshold."""
        return int(np.sum(ax_window < -self._cfg.harsh_brake_ms2))

    def count_harsh_accels(self, ax_window: np.ndarray) -> int:
        """Count samples with longitudinal acceleration > threshold."""
        return int(np.sum(ax_window > self._cfg.harsh_accel_ms2))

    def count_harsh_corners(self, ay_window: np.ndarray) -> int:
        """Count samples where lateral G-force exceeds the corner threshold."""
        return int(np.sum(np.abs(ay_window) > self._cfg.harsh_corner_ms2))

    def count_speeding(self, speed_window: np.ndarray) -> int:
        """Count GPS samples where speed exceeds the limit."""
        return int(np.sum(speed_window > self._cfg.speed_limit_ms))


# ─────────────────────────────────────────────
#  Window-level feature extractor
# ─────────────────────────────────────────────

class WindowFeatureExtractor:
    """
    Extracts a feature vector from one sliding window of sensor data.

    Args:
        detector: :class:`HarshEventDetector` instance.
    """

    def __init__(self, detector: HarshEventDetector) -> None:
        self._detector = detector

    def extract(
        self,
        accel_window: pd.DataFrame,
        gyro_window:  pd.DataFrame,
        gps_window:   pd.DataFrame,
        road_type:    RoadType,
    ) -> dict[str, float]:
        """
        Return a flat dictionary of features for one window.

        Args:
            accel_window: Accelerometer rows for this window.
            gyro_window:  Gyroscope rows for this window.
            gps_window:   GPS rows for this window.
            road_type:    Road type label for the trip.

        Returns:
            Dictionary mapping feature name → float value.
        """
        ax = accel_window["ax"].values
        ay = accel_window["ay"].values
        az = accel_window["az"].values
        gx = gyro_window["gx"].values
        gy = gyro_window["gy"].values
        gz = gyro_window["gz"].values
        sp = gps_window["speed_ms"].values if len(gps_window) > 0 else np.array([0.0])

        # ── Jerk (Δaccel / Δt) ─────────────────
        jerk_x = np.diff(ax) if len(ax) > 1 else np.array([0.0])
        jerk_y = np.diff(ay) if len(ay) > 1 else np.array([0.0])

        feats: dict[str, float] = {
            # Longitudinal acceleration stats
            "ax_mean":  float(np.mean(ax)),
            "ax_std":   float(np.std(ax)),
            "ax_max":   float(np.max(np.abs(ax))),
            "ax_rms":   float(np.sqrt(np.mean(ax ** 2))),

            # Lateral acceleration stats
            "ay_mean":  float(np.mean(ay)),
            "ay_std":   float(np.std(ay)),
            "ay_max":   float(np.max(np.abs(ay))),
            "ay_rms":   float(np.sqrt(np.mean(ay ** 2))),

            # Vertical acceleration stats
            "az_mean":  float(np.mean(az)),
            "az_std":   float(np.std(az)),

            # Jerk
            "jerk_x_std": float(np.std(jerk_x)),
            "jerk_x_max": float(np.max(np.abs(jerk_x))),
            "jerk_y_std": float(np.std(jerk_y)),

            # Gyroscope stats
            "gx_std":   float(np.std(gx)),
            "gy_std":   float(np.std(gy)),
            "gz_std":   float(np.std(gz)),
            "gz_max":   float(np.max(np.abs(gz))),

            # Speed stats from GPS
            "speed_mean": float(np.mean(sp)),
            "speed_std":  float(np.std(sp)),
            "speed_max":  float(np.max(sp)),

            # Harsh-event counts (normalised by window size)
            "harsh_brakes":  self._detector.count_harsh_brakes(ax)  / max(len(ax), 1),
            "harsh_accels":  self._detector.count_harsh_accels(ax)  / max(len(ax), 1),
            "harsh_corners": self._detector.count_harsh_corners(ay) / max(len(ay), 1),
            "speeding_frac": self._detector.count_speeding(sp)      / max(len(sp), 1),

            # Road-type encoding (1 = motorway, 0 = secondary)
            "is_motorway": float(road_type == RoadType.MOTORWAY),
        }
        return feats

    @property
    def feature_names(self) -> list[str]:
        """Return ordered list of feature names (matches extract output)."""
        dummy_accel = pd.DataFrame({"ax": [0.0], "ay": [0.0], "az": [0.0]})
        dummy_gyro  = pd.DataFrame({"gx": [0.0], "gy": [0.0], "gz": [0.0]})
        dummy_gps   = pd.DataFrame({"speed_ms": [0.0]})
        sample = self.extract(dummy_accel, dummy_gyro, dummy_gps, RoadType.MOTORWAY)
        return list(sample.keys())


# ─────────────────────────────────────────────
#  Trip-level feature engineer
# ─────────────────────────────────────────────

class FeatureEngineer:
    """
    Converts a list of :class:`TripData` objects into a
    (X, y) training matrix via a sliding-window approach.

    Args:
        config: Full application configuration.
    """

    def __init__(self, config: AppConfig) -> None:
        self._data_cfg  = config.data
        detector        = HarshEventDetector(config.threshold)
        self._extractor = WindowFeatureExtractor(detector)

    # ── public interface ───────────────────────

    def transform(
        self,
        trips: Sequence[TripData],
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """
        Slide a window over every trip and extract one feature vector
        per window.

        Args:
            trips: Iterable of loaded / synthetic trips.

        Returns:
            Tuple of:
                - ``X`` — DataFrame of shape (n_windows, n_features).
                - ``y`` — 1-D array of integer behaviour labels.
        """
        all_features: list[dict[str, float]] = []
        all_labels:   list[int]              = []

        for trip in trips:
            feats, labels = self._process_trip(trip)
            all_features.extend(feats)
            all_labels.extend(labels)

        if not all_features:
            raise ValueError("No windows extracted — check data / window_size.")

        X = pd.DataFrame(all_features)
        y = np.array(all_labels, dtype=np.int64)

        logger.info(
            "Feature matrix: %d windows × %d features  |  labels %s",
            len(X),
            X.shape[1],
            {BehaviorLabel(i).name: int((y == i).sum()) for i in np.unique(y)},
        )
        return X, y

    @property
    def feature_names(self) -> list[str]:
        """Ordered feature column names."""
        return self._extractor.feature_names

    # ── private helpers ────────────────────────

    def _process_trip(
        self,
        trip: TripData,
    ) -> tuple[list[dict[str, float]], list[int]]:
        """Slide window over one trip; return (feature_dicts, labels)."""
        win  = self._data_cfg.window_size
        step = max(1, int(win * (1.0 - self._data_cfg.window_overlap)))

        accel = trip.accel.reset_index(drop=True)
        gyro  = trip.gyro.reset_index(drop=True)
        gps   = trip.gps.reset_index(drop=True)

        # IMU is 10 Hz, GPS is 1 Hz in UAH-DriveSet
        imu_win  = win * 10
        imu_step = step * 10

        n_windows = max(0, (len(accel) - imu_win) // imu_step + 1)

        feats:  list[dict[str, float]] = []
        labels: list[int]              = []

        for w in range(n_windows):
            i_start = w * imu_step
            i_end   = i_start + imu_win
            g_start = w * step
            g_end   = g_start + win

            accel_win = accel.iloc[i_start:i_end]
            gyro_win  = gyro.iloc[i_start:i_end]
            gps_win   = gps.iloc[g_start:g_end]

            if len(accel_win) < 5:   # skip tiny tail windows
                continue

            feat_dict = self._extractor.extract(
                accel_win, gyro_win, gps_win, trip.road_type
            )
            feats.append(feat_dict)
            labels.append(trip.behavior.value)

        return feats, labels
