"""
ML model definitions for driving behaviour classification.

Design:
    BaseModel (ABC)          — defines the interface every model must satisfy
    ├── RandomForestModel    — ensemble tree-based classifier
    ├── GradientBoostingModel — boosted tree classifier
    └── SVMModel             — Support Vector Machine

All models are wrapped with a StandardScaler so callers never
need to worry about scaling.
"""

from __future__ import annotations

import logging
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from config.settings import AppConfig, ModelType, TrainingConfig

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Abstract base
# ─────────────────────────────────────────────

class BaseModel(ABC):
    """
    Contract every driving-behaviour classifier must implement.

    Sub-classes wrap a scikit-learn Pipeline so scaling + prediction
    are always handled together.
    """

    def __init__(self, config: TrainingConfig) -> None:
        self._cfg:      TrainingConfig  = config
        self._pipeline: Pipeline | None = None
        self._is_fitted: bool           = False

    # ── required interface ─────────────────────

    @abstractmethod
    def _build_pipeline(self) -> Pipeline:
        """Construct and return the sklearn Pipeline (not yet fitted)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable model name."""
        ...

    # ── concrete methods ───────────────────────

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "BaseModel":
        """
        Fit the model on training data.

        Args:
            X: Feature matrix (n_samples × n_features).
            y: Integer label vector.

        Returns:
            Self, allowing method chaining.
        """
        self._pipeline = self._build_pipeline()
        logger.info("Training %s on %d samples ...", self.name, len(X))
        self._pipeline.fit(X, y)
        self._is_fitted = True
        logger.info("%s training complete.", self.name)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict behaviour labels for feature matrix X.

        Args:
            X: Feature matrix.

        Returns:
            Array of integer predictions.

        Raises:
            RuntimeError: If the model has not been fitted yet.
        """
        self._assert_fitted()
        return self._pipeline.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return class-probability matrix (n_samples × n_classes).

        Raises:
            RuntimeError: If the model has not been fitted yet.
            AttributeError: If the underlying estimator lacks ``predict_proba``.
        """
        self._assert_fitted()
        return self._pipeline.predict_proba(X)

    def save(self, path: Path) -> None:
        """Serialise the fitted pipeline to disk with pickle."""
        self._assert_fitted()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self._pipeline, fh)
        logger.info("Model saved → %s", path)

    @classmethod
    def load(cls, path: Path, config: TrainingConfig) -> "BaseModel":
        """
        Deserialise a pipeline previously saved with :meth:`save`.

        Args:
            path:   File path written by :meth:`save`.
            config: Training configuration (used to reconstruct the shell).

        Returns:
            A fitted model instance.
        """
        instance = cls.__new__(cls)
        instance._cfg = config
        with open(path, "rb") as fh:
            instance._pipeline = pickle.load(fh)
        instance._is_fitted = True
        logger.info("Model loaded ← %s", path)
        return instance

    def __repr__(self) -> str:
        status = "fitted" if self._is_fitted else "untrained"
        return f"{self.__class__.__name__}(status={status})"

    # ── private helpers ────────────────────────

    def _assert_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                f"{self.name} has not been fitted yet. Call .fit() first."
            )


# ─────────────────────────────────────────────
#  Concrete implementations
# ─────────────────────────────────────────────

class RandomForestModel(BaseModel):
    """
    Random Forest driving behaviour classifier.

    Recommended for this task: strong out-of-the-box performance,
    built-in feature importance, and tolerance for noisy IMU data.
    """

    @property
    def name(self) -> str:
        return "RandomForest"

    def _build_pipeline(self) -> Pipeline:
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    RandomForestClassifier(
                n_estimators=self._cfg.rf_n_estimators,
                max_depth=self._cfg.rf_max_depth,
                class_weight=self._cfg.rf_class_weight,
                random_state=self._cfg.random_state,
                n_jobs=self._cfg.n_jobs,
            )),
        ])

    @property
    def feature_importances(self) -> np.ndarray | None:
        """Return feature importance scores (only after fitting)."""
        if not self._is_fitted:
            return None
        return self._pipeline.named_steps["clf"].feature_importances_


class GradientBoostingModel(BaseModel):
    """
    Gradient Boosting classifier — often wins on tabular data benchmarks.
    Slower to train than RF but typically yields tighter decision boundaries.
    """

    @property
    def name(self) -> str:
        return "GradientBoosting"

    def _build_pipeline(self) -> Pipeline:
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    GradientBoostingClassifier(
                n_estimators=self._cfg.gb_n_estimators,
                learning_rate=self._cfg.gb_learning_rate,
                max_depth=self._cfg.gb_max_depth,
                random_state=self._cfg.random_state,
            )),
        ])


class SVMModel(BaseModel):
    """
    Radial-Basis-Function SVM classifier.

    Works best when features are well-scaled (handled inside the
    Pipeline). Enables probability calibration for downstream scoring.
    """

    @property
    def name(self) -> str:
        return "SVM"

    def _build_pipeline(self) -> Pipeline:
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    SVC(
                C=self._cfg.svm_C,
                kernel=self._cfg.svm_kernel,
                probability=self._cfg.svm_probability,
                random_state=self._cfg.random_state,
            )),
        ])


# ─────────────────────────────────────────────
#  Factory
# ─────────────────────────────────────────────

class ModelFactory:
    """
    Creates model instances by :class:`ModelType` enum value.

    Usage::

        model = ModelFactory.create(ModelType.RANDOM_FOREST, config.training)
    """

    _REGISTRY: dict[ModelType, type[BaseModel]] = {
        ModelType.RANDOM_FOREST:     RandomForestModel,
        ModelType.GRADIENT_BOOSTING: GradientBoostingModel,
        ModelType.SVM:               SVMModel,
    }

    @classmethod
    def create(cls, model_type: ModelType, config: TrainingConfig) -> BaseModel:
        """
        Instantiate a model of the given type.

        Args:
            model_type: One of the :class:`ModelType` enum values.
            config:     Training configuration.

        Returns:
            An unfitted :class:`BaseModel` sub-class instance.

        Raises:
            ValueError: If ``model_type`` is not registered.
        """
        klass = cls._REGISTRY.get(model_type)
        if klass is None:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Available: {list(cls._REGISTRY)}"
            )
        return klass(config)

    @classmethod
    def all_models(cls, config: TrainingConfig) -> list[BaseModel]:
        """Return one instance of every registered model type."""
        return [cls.create(mt, config) for mt in ModelType]
