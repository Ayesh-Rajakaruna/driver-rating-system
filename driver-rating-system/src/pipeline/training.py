"""
End-to-end training pipeline.

Orchestrates: data loading → feature engineering → train/test split
→ model training → evaluation → scoring demo.

The pipeline follows the *Template Method* pattern: the high-level
sequence is fixed in :meth:`TrainingPipeline.run`, while each step
delegates to a specialised component.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from config.settings import AppConfig, ModelType
from data.loader import SyntheticDataGenerator, TripData, UAHDataLoader
from evaluation.evaluator import EvaluationResult, ModelEvaluator
from features.engineer import FeatureEngineer
from models.classifiers import BaseModel, ModelFactory
from scoring.scorer import ProbabilityScorer, ScoreInterpreter

logger = logging.getLogger(__name__)


class TrainingPipeline:
    """
    Coordinates the full ML lifecycle for driver safety rating.

    Args:
        config:       Application configuration.
        use_real_data: If ``True``, attempt to load the UAH-DriveSet;
                       falls back to synthetic data automatically.
    """

    def __init__(
        self,
        config:        AppConfig,
        use_real_data: bool = True,
    ) -> None:
        self._cfg           = config
        self._use_real_data = use_real_data

        # Components (initialised in run())
        self._engineer:  FeatureEngineer | None  = None
        self._evaluator: ModelEvaluator  | None  = None

    # ── public entry point ─────────────────────

    def run(self) -> dict[str, EvaluationResult]:
        """
        Execute the full training and evaluation pipeline.

        Steps:
            1. Load data (real or synthetic).
            2. Extract features via sliding windows.
            3. Train / test split (stratified).
            4. Train all registered models.
            5. Cross-validate each model.
            6. Evaluate on the held-out test set.
            7. Demonstrate the safety scorer on a sample.

        Returns:
            Mapping of model name → :class:`EvaluationResult`.
        """
        logger.info("═" * 55)
        logger.info("  Driver Safety Rating — Training Pipeline")
        logger.info("═" * 55)

        # 1 ── Load data ────────────────────────
        trips = self._load_data()

        # 2 ── Feature engineering ──────────────
        self._engineer = FeatureEngineer(self._cfg)
        X, y = self._engineer.transform(trips)

        # 3 ── Train / test split ───────────────
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size    = self._cfg.data.test_size,
            random_state = self._cfg.data.random_state,
            stratify     = y,
        )
        logger.info(
            "Split: %d train  |  %d test  |  features: %d",
            len(X_train), len(X_test), X.shape[1],
        )

        # 4 ── Train all models ─────────────────
        models = ModelFactory.all_models(self._cfg.training)
        for model in models:
            model.fit(X_train, y_train)

        # 5 ── Cross-validation ─────────────────
        self._cross_validate(models, X_train, y_train)

        # 6 ── Evaluate on test set ─────────────
        self._evaluator = ModelEvaluator(self._cfg)
        results: dict[str, EvaluationResult] = {}
        feature_names = self._engineer.feature_names

        for model in models:
            result = self._evaluator.evaluate(
                model,
                X_test,
                y_test,
                feature_names=feature_names,
            )
            results[model.name] = result

        # Comparison table
        self._evaluator.compare(list(results.values()))

        # 7 ── Safety score demonstration ───────
        self._demo_scoring(models[0], X_test)

        return results

    # ── private helpers ────────────────────────

    def _load_data(self) -> list[TripData]:
        if self._use_real_data:
            try:
                loader = UAHDataLoader(self._cfg)
                trips  = loader.load_all()
                if trips:
                    return trips
                logger.warning("UAH-DriveSet folder is empty — using synthetic data.")
            except FileNotFoundError as exc:
                logger.warning("%s — falling back to synthetic data.", exc)

        gen = SyntheticDataGenerator(
            self._cfg,
            n_trips=90,          # 30 per class
            seed=self._cfg.data.random_state,
        )
        return gen.generate()

    def _cross_validate(
        self,
        models:  list[BaseModel],
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        n_folds: int = 5,
    ) -> None:
        """Run stratified k-fold CV and log mean ± std F1."""
        print("\n" + "─" * 55)
        print(f"  {n_folds}-Fold Cross-Validation (train set)")
        print("─" * 55)

        cv = StratifiedKFold(
            n_splits=n_folds,
            shuffle=True,
            random_state=self._cfg.data.random_state,
        )
        for model in models:
            scores = cross_val_score(
                model._pipeline,   # use the sklearn estimator directly
                X_train, y_train,
                cv=cv,
                scoring="f1_macro",
                n_jobs=self._cfg.training.n_jobs,
            )
            print(
                f"  {model.name:<22} F1-macro = "
                f"{scores.mean():.4f}  ±  {scores.std():.4f}"
            )

    def _demo_scoring(
        self,
        model:  BaseModel,
        X_test: pd.DataFrame,
        n_demo: int = 5,
    ) -> None:
        """Show per-sample safety scores for the first n_demo windows."""
        print("\n" + "═" * 55)
        print("  Safety Score Demonstration (first windows in test set)")
        print("═" * 55)

        scorer      = ProbabilityScorer(self._cfg)
        interpreter = ScoreInterpreter()

        sample   = X_test.head(n_demo)
        trip_score = scorer.score_trip(sample, model)
        window_scores = scorer.score_batch(sample, model)

        for i, ws in enumerate(window_scores, start=1):
            info = interpreter.interpret(ws)
            print(
                f"  Window {i:>2}: {float(ws):5.1f}/100  "
                f"[{info['band']:<10}]  {info['message']}"
            )

        print("─" * 55)
        trip_info = interpreter.interpret(trip_score)
        print(
            f"  Trip average : {trip_score:5.1f}/100  "
            f"[{trip_info['band']}]  {trip_info['message']}"
        )
        print("═" * 55 + "\n")
