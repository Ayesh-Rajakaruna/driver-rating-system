"""
Model evaluation: metrics, confusion matrices, and feature-importance plots.

Produces both console-readable tables and persisted PNG figures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # headless rendering — no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
)

from config.settings import AppConfig, BehaviorLabel
from models.classifiers import BaseModel, RandomForestModel

logger = logging.getLogger(__name__)

_LABEL_NAMES = [lbl.name for lbl in BehaviorLabel]


# ─────────────────────────────────────────────
#  Value object: evaluation result
# ─────────────────────────────────────────────

@dataclass
class EvaluationResult:
    """
    Holds all computed metrics for one model evaluation run.

    Attributes:
        model_name:        Name of the evaluated model.
        accuracy:          Overall accuracy (0–1).
        precision_macro:   Macro-averaged precision.
        recall_macro:      Macro-averaged recall.
        f1_macro:          Macro-averaged F1 score.
        f1_per_class:      F1 per behaviour class.
        confusion:         Confusion matrix (n_classes × n_classes).
        report_text:       Full scikit-learn classification report string.
    """
    model_name:     str
    accuracy:       float
    precision_macro: float
    recall_macro:   float
    f1_macro:       float
    f1_per_class:   dict[str, float]
    confusion:      np.ndarray
    report_text:    str

    def summary(self) -> str:
        """One-line summary string for quick inspection."""
        return (
            f"[{self.model_name}] "
            f"Acc={self.accuracy:.4f}  "
            f"Prec={self.precision_macro:.4f}  "
            f"Rec={self.recall_macro:.4f}  "
            f"F1={self.f1_macro:.4f}"
        )


# ─────────────────────────────────────────────
#  Evaluator
# ─────────────────────────────────────────────

class ModelEvaluator:
    """
    Evaluates a trained :class:`BaseModel` on a held-out test set.

    Responsibilities:
        * Compute classification metrics (accuracy, precision, recall, F1).
        * Plot and save confusion matrix.
        * Plot and save feature-importance chart (Random Forest only).
        * Return a structured :class:`EvaluationResult`.

    Args:
        config: Application configuration (used for output paths).
    """

    def __init__(self, config: AppConfig) -> None:
        self._figures_dir = Path(config.output.figures_dir)
        self._figures_dir.mkdir(parents=True, exist_ok=True)

    # ── public interface ───────────────────────

    def evaluate(
        self,
        model:           BaseModel,
        X_test:          pd.DataFrame,
        y_test:          np.ndarray,
        feature_names:   list[str] | None = None,
        save_plots:      bool = True,
    ) -> EvaluationResult:
        """
        Run full evaluation on test data.

        Args:
            model:          A **fitted** :class:`BaseModel`.
            X_test:         Test feature matrix.
            y_test:         True integer labels.
            feature_names:  Column names (for importance plot).
            save_plots:     Whether to write PNG files.

        Returns:
            :class:`EvaluationResult` with all metrics populated.
        """
        y_pred = model.predict(X_test)

        result = EvaluationResult(
            model_name      = model.name,
            accuracy        = float(accuracy_score(y_test, y_pred)),
            precision_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
            recall_macro    = float(recall_score(y_test, y_pred, average="macro",    zero_division=0)),
            f1_macro        = float(f1_score(y_test, y_pred, average="macro",        zero_division=0)),
            f1_per_class    = self._f1_per_class(y_test, y_pred),
            confusion       = confusion_matrix(y_test, y_pred),
            report_text     = classification_report(
                y_test, y_pred,
                target_names=_LABEL_NAMES,
                zero_division=0,
            ),
        )

        logger.info(result.summary())
        print("\n" + "─" * 60)
        print(f"  Evaluation — {result.model_name}")
        print("─" * 60)
        print(result.report_text)

        if save_plots:
            self._plot_confusion_matrix(result)
            if isinstance(model, RandomForestModel) and feature_names:
                self._plot_feature_importance(model, feature_names)

        return result

    def compare(self, results: list[EvaluationResult]) -> pd.DataFrame:
        """
        Build a comparison DataFrame from multiple evaluation results.

        Args:
            results: List of :class:`EvaluationResult` objects.

        Returns:
            DataFrame with one row per model and metric columns.
        """
        rows = []
        for r in results:
            row = {
                "Model":     r.model_name,
                "Accuracy":  round(r.accuracy, 4),
                "Precision": round(r.precision_macro, 4),
                "Recall":    round(r.recall_macro, 4),
                "F1 (macro)": round(r.f1_macro, 4),
            }
            for cls_name, f1_val in r.f1_per_class.items():
                row[f"F1_{cls_name}"] = round(f1_val, 4)
            rows.append(row)

        df = pd.DataFrame(rows).set_index("Model")
        print("\n" + "=" * 60)
        print("  Model Comparison")
        print("=" * 60)
        print(df.to_string())
        return df

    # ── private plot helpers ───────────────────

    def _plot_confusion_matrix(self, result: EvaluationResult) -> None:
        fig, ax = plt.subplots(figsize=(7, 6))
        disp = ConfusionMatrixDisplay(
            confusion_matrix=result.confusion,
            display_labels=_LABEL_NAMES,
        )
        disp.plot(ax=ax, cmap="Blues", colorbar=False)
        ax.set_title(f"Confusion Matrix — {result.model_name}", fontsize=13)
        plt.tight_layout()
        save_path = self._figures_dir / f"confusion_{result.model_name}.png"
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        logger.info("Confusion matrix saved → %s", save_path)

    def _plot_feature_importance(
        self,
        model:         RandomForestModel,
        feature_names: list[str],
        top_n:         int = 15,
    ) -> None:
        importances = model.feature_importances
        if importances is None:
            return

        n = min(top_n, len(feature_names))
        idx = np.argsort(importances)[::-1][:n]
        top_names  = [feature_names[i] for i in idx]
        top_scores = importances[idx]

        fig, ax = plt.subplots(figsize=(9, 5))
        bars = ax.barh(
            range(n), top_scores[::-1],
            color=sns.color_palette("Blues_d", n),
            edgecolor="white",
        )
        ax.set_yticks(range(n))
        ax.set_yticklabels(top_names[::-1], fontsize=10)
        ax.set_xlabel("Importance Score", fontsize=11)
        ax.set_title(f"Top {n} Feature Importances — {model.name}", fontsize=13)
        plt.tight_layout()
        save_path = self._figures_dir / f"feature_importance_{model.name}.png"
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        logger.info("Feature importance plot saved → %s", save_path)

    # ── static helpers ─────────────────────────

    @staticmethod
    def _f1_per_class(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
        scores = f1_score(y_true, y_pred, average=None, zero_division=0)
        # scores length matches number of unique classes seen
        result = {}
        for i, score in enumerate(scores):
            try:
                name = BehaviorLabel(i).name
            except ValueError:
                name = str(i)
            result[name] = float(score)
        return result
