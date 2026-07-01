"""
Configuration settings for the Driver Safety Rating System.

All tunable constants live here — no magic numbers scattered
across the codebase.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


# ─────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────

class BehaviorLabel(Enum):
    """Driving behaviour classes from the UAH-DriveSet."""
    NORMAL     = 0
    DROWSY     = 1
    AGGRESSIVE = 2


class RoadType(Enum):
    """Road types present in UAH-DriveSet."""
    MOTORWAY  = "Motorway"
    SECONDARY = "Secondary"


class ModelType(Enum):
    """Supported ML classifiers."""
    RANDOM_FOREST     = auto()
    GRADIENT_BOOSTING = auto()
    SVM               = auto()


# ─────────────────────────────────────────────
#  Data settings
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class DataConfig:
    """Parameters for loading and windowing raw sensor data."""

    # Root folder that contains UAH-DriveSet trip sub-folders
    dataset_root: Path = Path("data/UAH-DriveSet")

    # Sliding-window length (samples).  UAH GPS = 1 Hz → 30 s window
    window_size: int   = 30
    # Overlap between consecutive windows (fraction 0–1)
    window_overlap: float = 0.5

    # Column names expected in each raw file
    gps_columns: tuple = (
        "timestamp", "speed_ms", "lat", "lon", "altitude",
        "vertical_accuracy", "horizontal_accuracy",
    )
    accel_columns: tuple = ("timestamp", "ax", "ay", "az")
    gyro_columns:  tuple = ("timestamp", "gx", "gy", "gz")
    semantic_columns: tuple = ("timestamp", "behavior_label")

    # Fraction of data reserved for testing
    test_size: float  = 0.20
    random_state: int = 42


# ─────────────────────────────────────────────
#  Feature engineering thresholds
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class ThresholdConfig:
    """
    G-force thresholds (in m/s²) used to flag harsh driving events.

    References:
        Castignani et al. (2015) — IEEE ITS Magazine
        Geotab Driver Safety Scorecard White Paper
    """
    # Longitudinal deceleration threshold → harsh brake
    harsh_brake_ms2:    float = 3.5   # ≈ 0.36 g
    # Longitudinal acceleration threshold → harsh acceleration
    harsh_accel_ms2:    float = 2.9   # ≈ 0.30 g
    # Lateral acceleration threshold → harsh cornering
    harsh_corner_ms2:   float = 2.0   # ≈ 0.20 g
    # Speed threshold above which speeding is flagged (m/s)
    speed_limit_ms:     float = 33.33 # ≈ 120 km/h (motorway)


# ─────────────────────────────────────────────
#  Scoring weights
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class ScoringConfig:
    """
    Penalty weights for each event type in the composite safety score.

    Score starts at 100 and is reduced per event occurrence.
    Weights are normalised per km of driving distance.
    """
    weight_harsh_brake:    float = 3.0
    weight_harsh_accel:    float = 2.0
    weight_harsh_corner:   float = 2.5
    weight_speeding:       float = 4.0
    # Minimum achievable score (floor)
    score_floor:           float = 0.0


# ─────────────────────────────────────────────
#  Training settings
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class TrainingConfig:
    """Hyper-parameters for model training."""

    # ── Random Forest ──────────────────────────
    rf_n_estimators:  int   = 200
    rf_max_depth:     int   = 12
    rf_class_weight:  str   = "balanced"

    # ── Gradient Boosting ──────────────────────
    gb_n_estimators:  int   = 150
    gb_learning_rate: float = 0.08
    gb_max_depth:     int   = 5

    # ── SVM ────────────────────────────────────
    svm_C:            float = 1.0
    svm_kernel:       str   = "rbf"
    svm_probability:  bool  = True

    random_state:     int   = 42
    n_jobs:           int   = -1   # use all CPU cores


# ─────────────────────────────────────────────
#  Output paths
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class OutputConfig:
    """Where to save artefacts produced during training."""
    results_dir:    Path = Path("outputs/results")
    models_dir:     Path = Path("outputs/models")
    figures_dir:    Path = Path("outputs/figures")


# ─────────────────────────────────────────────
#  Master config (single object passed around)
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class AppConfig:
    """
    Top-level configuration object.

    Usage::

        from config.settings import AppConfig
        cfg = AppConfig()
        print(cfg.data.window_size)
    """
    data:      DataConfig      = field(default_factory=DataConfig)
    threshold: ThresholdConfig = field(default_factory=ThresholdConfig)
    scoring:   ScoringConfig   = field(default_factory=ScoringConfig)
    training:  TrainingConfig  = field(default_factory=TrainingConfig)
    output:    OutputConfig     = field(default_factory=OutputConfig)
