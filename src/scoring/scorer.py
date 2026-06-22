"""
Safety Scorer: converts model output into a human-readable 0–100 safety score.

Two scoring strategies are provided:
    PenaltyScorer   — rule-based, subtracts points for harsh-event rates
    ProbabilityScorer — ML-based, uses predicted probabilities directly

Both implement the :class:`BaseSafetyScorer` interface.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from config.settings import AppConfig, BehaviorLabel, ScoringConfig
from models.classifiers import BaseModel

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Abstract base
# ─────────────────────────────────────────────

class BaseSafetyScorer(ABC):
    """
    Interface for all safety scoring strategies.

    A safety score is a float in [0, 100] where:
        100 = perfectly safe
          0 = maximally unsafe
    """

    @abstractmethod
    def score_trip(
        self,
        features: pd.DataFrame,
        model:    BaseModel,
    ) -> float:
        """
        Compute a scalar safety score for one trip's feature matrix.

        Args:
            features: Window-level feature rows for a single trip.
            model:    A fitted classifier.

        Returns:
            Safety score in [0, 100].
        """
        ...

    @abstractmethod
    def score_batch(
        self,
        features: pd.DataFrame,
        model:    BaseModel,
    ) -> np.ndarray:
        """
        Score each window individually (used for timeline visualisation).

        Args:
            features: Feature matrix for multiple windows.
            model:    A fitted classifier.

        Returns:
            Array of per-window scores, shape (n_windows,).
        """
        ...


# ─────────────────────────────────────────────
#  Strategy 1: penalty-based
# ─────────────────────────────────────────────

class PenaltyScorer(BaseSafetyScorer):
    """
    Rule-based scoring: starts at 100, deducts penalties for harsh events.

    Penalty per km formula (Castignani-style)::

        score = 100
              - w_brake  × (harsh_brake_rate  × 1000)
              - w_accel  × (harsh_accel_rate  × 1000)
              - w_corner × (harsh_corner_rate × 1000)
              - w_speed  × (speeding_fraction × 100)

    Rates are already normalised by window size in :mod:`features.engineer`.

    Args:
        config: Full application configuration.
    """

    def __init__(self, config: AppConfig) -> None:
        self._cfg: ScoringConfig = config.scoring

    def score_trip(
        self,
        features: pd.DataFrame,
        model:    BaseModel,       # not used in rule-based scorer
    ) -> float:
        window_scores = self.score_batch(features, model)
        return float(np.clip(np.mean(window_scores), self._cfg.score_floor, 100.0))

    def score_batch(
        self,
        features: pd.DataFrame,
        model:    BaseModel,
    ) -> np.ndarray:
        cfg = self._cfg
        raw = (
            100.0
            - cfg.weight_harsh_brake   * features["harsh_brakes"]  * 100
            - cfg.weight_harsh_accel   * features["harsh_accels"]  * 100
            - cfg.weight_harsh_corner  * features["harsh_corners"] * 100
            - cfg.weight_speeding      * features["speeding_frac"] * 100
        )
        return np.clip(raw.values, cfg.score_floor, 100.0)


# ─────────────────────────────────────────────
#  Strategy 2: probability-based
# ─────────────────────────────────────────────

class ProbabilityScorer(BaseSafetyScorer):
    """
    ML-based scoring: uses the classifier's predicted class probabilities.

    Score formula::

        score_window = P(NORMAL) × 100
                     + P(DROWSY) × 40
                     + P(AGGRESSIVE) × 0

    The final trip score is the mean over all windows.

    Args:
        config: Full application configuration (not used directly here,
                but kept for interface consistency).
    """

    # Class weights for the probability-weighted sum
    _CLASS_SCORES: dict[int, float] = {
        BehaviorLabel.NORMAL.value:     100.0,
        BehaviorLabel.DROWSY.value:      40.0,
        BehaviorLabel.AGGRESSIVE.value:   0.0,
    }

    def __init__(self, config: AppConfig) -> None:
        self._floor: float = config.scoring.score_floor

    def score_trip(
        self,
        features: pd.DataFrame,
        model:    BaseModel,
    ) -> float:
        window_scores = self.score_batch(features, model)
        return float(np.clip(np.mean(window_scores), self._floor, 100.0))

    def score_batch(
        self,
        features: pd.DataFrame,
        model:    BaseModel,
    ) -> np.ndarray:
        proba = model.predict_proba(features)   # (n_windows, n_classes)
        weights = np.array([
            self._CLASS_SCORES.get(i, 50.0)
            for i in range(proba.shape[1])
        ])
        scores = proba @ weights                # dot product
        return np.clip(scores, self._floor, 100.0)


# ─────────────────────────────────────────────
#  Score interpreter
# ─────────────────────────────────────────────

class ScoreInterpreter:
    """
    Converts a numeric safety score into a human-readable rating band
    and coaching message — similar to insurance telematics feedback.

    Bands::

        90–100  Excellent   — consistently safe driving
        75–89   Good        — minor improvements needed
        60–74   Fair        — moderate risk events detected
        45–59   Poor        — frequent unsafe behaviours
         0–44   Critical    — immediate coaching required
    """

    _BANDS: list[tuple[float, str, str]] = [
        (90, "Excellent", "Great driving — keep it up!"),
        (75, "Good",      "Good overall. Watch your cornering speed."),
        (60, "Fair",      "Moderate risk events detected. Reduce harsh braking."),
        (45, "Poor",      "Frequent unsafe events. Consider a refresher course."),
        ( 0, "Critical",  "High accident risk. Immediate coaching required."),
    ]

    @classmethod
    def interpret(cls, score: float) -> dict[str, str]:
        """
        Map a numeric score to a rating band and feedback message.

        Args:
            score: Safety score in [0, 100].

        Returns:
            Dictionary with keys ``score``, ``band``, ``message``.
        """
        for threshold, band, message in cls._BANDS:
            if score >= threshold:
                return {
                    "score":   f"{score:.1f}",
                    "band":    band,
                    "message": message,
                }
        # Fallback (should not be reached with valid scores)
        return {"score": f"{score:.1f}", "band": "Critical", "message": ""}
