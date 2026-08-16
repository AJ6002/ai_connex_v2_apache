"""
losses.py — Custom regression loss functions
============================================
Implements asymmetric RUL scoring (PHM08 convention) where predicting
"engine fails later than it actually does" is penalized far more heavily
than predicting "engine fails earlier" (early replacement is safe,
running to catastrophic failure is not).
"""

from __future__ import annotations
import numpy as np
from typing import Callable


def asymmetric_rul_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    PHM08 Asymmetric Scoring Function for Remaining Useful Life.

    For each prediction:
      - If predicted RUL < true RUL (early prediction): s = exp(-d/13) - 1
      - If predicted RUL > true RUL (late prediction):  s = exp(+d/10) - 1

    Where d = y_pred - y_true (error).
    Late predictions are penalized with a steeper exponential.

    Lower score = better model.
    """
    d = y_pred - y_true
    scores = np.where(
        d < 0,
        np.exp(-d / 13.0) - 1,   # early prediction — lighter penalty
        np.exp(d / 10.0) - 1,    # late prediction  — heavier penalty
    )
    return float(np.mean(scores))


def huber_loss(y_true: np.ndarray, y_pred: np.ndarray, delta: float = 1.0) -> float:
    """
    Huber loss: quadratic for small errors, linear for large errors.
    More robust to outliers than MSE.
    """
    residual = np.abs(y_true - y_pred)
    loss = np.where(
        residual <= delta,
        0.5 * residual ** 2,
        delta * (residual - 0.5 * delta),
    )
    return float(np.mean(loss))


def get_sklearn_scorer(loss_name: str) -> str:
    """
    Map a loss name to the corresponding sklearn scorer string for
    use in RandomizedSearchCV or cross_val_score.
    """
    mapping = {
        "rmse": "neg_root_mean_squared_error",
        "mae":  "neg_mean_absolute_error",
        "r2":   "r2",
        "mape": "neg_mean_absolute_percentage_error",
    }
    if loss_name not in mapping:
        raise ValueError(f"Unknown loss: '{loss_name}'. Available: {list(mapping.keys())}")
    return mapping[loss_name]
