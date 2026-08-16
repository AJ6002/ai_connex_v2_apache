# aiconnex_ml/shared/ensemble.py
"""
Stacked Ensemble Meta-Learner (Phase 5c)
==========================================
Fits a non-negative Ridge regression on out-of-fold cross-validation
predictions from K base models to produce an optimally-weighted ensemble.

    y_hat = sum(w_k * Model_k(x))   s.t. w_k >= 0

Uses sklearn.linear_model.Ridge(positive=True) which enforces non-negativity
on coefficients, ensuring every base model contributes positively or is
zeroed out — never anti-correlated.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge


class StackedEnsembleMetaLearner:
    """Non-negative Ridge meta-learner over base model OOF predictions."""

    def __init__(self, alpha: float = 1.0):
        self._alpha = alpha
        self._ridge: Ridge | None = None

    @property
    def is_fitted(self) -> bool:
        return self._ridge is not None

    def fit(self, oof_matrix: np.ndarray, y_true: np.ndarray) -> None:
        """Fit the meta-learner on out-of-fold prediction matrix.

        Args:
            oof_matrix: shape (N, K) — OOF predictions from K base models.
            y_true: shape (N,) — ground truth target values.

        Raises:
            ValueError: If fewer than 2 samples are provided.
        """
        if oof_matrix.shape[0] < 2:
            raise ValueError("Meta-learner requires at least 2 samples to fit.")

        self._ridge = Ridge(alpha=self._alpha, positive=True, fit_intercept=True)
        self._ridge.fit(oof_matrix, y_true)

    def predict(self, base_predictions: np.ndarray) -> np.ndarray:
        """Predict using the fitted meta-learner weights.

        Args:
            base_predictions: shape (M, K) — predictions from K base models on M samples.

        Returns:
            np.ndarray of shape (M,) — weighted ensemble predictions.

        Raises:
            RuntimeError: If called before fit().
        """
        if not self.is_fitted:
            raise RuntimeError("Meta-learner is not fitted. Call fit() first.")
        return self._ridge.predict(base_predictions)

    def get_weights(self) -> np.ndarray:
        """Return the K non-negative meta-learner coefficients.

        Returns:
            np.ndarray of shape (K,) — non-negative weights for each base model.

        Raises:
            RuntimeError: If called before fit().
        """
        if not self.is_fitted:
            raise RuntimeError("Meta-learner is not fitted. Call fit() first.")
        return self._ridge.coef_
