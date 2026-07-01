"""
Driver Safety Rating System — entry point.

Run:
    python main.py

The pipeline will:
    1. Try to load UAH-DriveSet from data/UAH-DriveSet/
    2. Fall back to synthetic data automatically if the folder is absent
    3. Train Random Forest, Gradient Boosting, and SVM classifiers
    4. Run 5-fold cross-validation on each
    5. Evaluate all models on the held-out test set
    6. Print metrics and save confusion-matrix/feature-importance plots
    7. Demonstrate the 0–100 safety scorer
"""

import logging
import sys
from pathlib import Path

from config.settings import AppConfig
from pipeline.training import TrainingPipeline


# ─────────────────────────────────────────────
#  Logging configuration
# ─────────────────────────────────────────────

def configure_logging(level: int = logging.INFO) -> None:
    """Set up root logger with a clean, timestamped format."""
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
    logging.basicConfig(
        level   = level,
        format  = fmt,
        datefmt = "%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Silence noisy third-party loggers
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


# ─────────────────────────────────────────────
#  Output directories
# ─────────────────────────────────────────────

def ensure_output_dirs(config: AppConfig) -> None:
    """Create output directories if they don't already exist."""
    for path in (
        config.output.results_dir,
        config.output.models_dir,
        config.output.figures_dir,
    ):
        Path(path).mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    logger.info("Initialising configuration …")
    config = AppConfig()
    ensure_output_dirs(config)

    pipeline = TrainingPipeline(config, use_real_data=True)

    try:
        results = pipeline.run()
        best = max(results.values(), key=lambda r: r.f1_macro)
        logger.info(
            "Best model: %s  (F1-macro = %.4f)",
            best.model_name,
            best.f1_macro,
        )
    except Exception:
        logger.exception("Pipeline failed with an unexpected error.")
        sys.exit(1)


if __name__ == "__main__":
    main()
