"""
operating_modes.py — OperatingModeDetector: prevent regime changes from being flagged
======================================================================================
The #1 source of alarm fatigue: a model trained on steady-state data flags
every startup/shutdown transition as an anomaly.

This module:
  1. Detects the current operating mode from the mode_column
  2. Filters training data per mode for per-mode model fitting
  3. Applies per-mode thresholds during inference
  4. Logs when a legitimate mode change occurs (not an anomaly)
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd


class OperatingModeDetector:
    """
    Manages per-operating-mode data partitioning and threshold routing.

    Usage:
        detector = OperatingModeDetector(manifest)
        X_normal_by_mode = detector.split_by_mode(df_train, feature_cols)
        is_mode_anomaly = detector.is_mode_transition(current_mode)
    """

    def __init__(self, manifest: Dict[str, Any]):
        mode_cfg = manifest.get("operating_modes", {})
        self.enabled = mode_cfg.get("enabled", False)
        self.mode_column = mode_cfg.get("mode_column")
        self.known_modes: List[str] = [str(m) for m in mode_cfg.get("known_modes", [])]
        self.mode_thresholds: Dict[str, float] = {}
        self.manifest = manifest

    def is_configured(self) -> bool:
        return self.enabled and bool(self.mode_column)

    def auto_discover_modes(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        n_clusters: int = 3,
    ) -> pd.DataFrame:
        """
        G-08 Fix: Auto-discover operating modes via KMeans clustering
        when no explicit mode_column is provided in raw data.
        """
        from sklearn.cluster import KMeans
        df = df.copy()
        X = df[feature_cols].select_dtypes(include=[np.number]).fillna(0)
        km = KMeans(n_clusters=min(n_clusters, max(1, len(df))), random_state=42)
        clusters = km.fit_predict(X)
        self.mode_column = "_auto_discovered_mode"
        df[self.mode_column] = [f"mode_{c}" for c in clusters]
        self.enabled = True
        self.known_modes = [f"mode_{c}" for c in range(n_clusters)]
        print(f"[ModeDetector] Auto-discovered {n_clusters} operating modes via KMeans.")
        return df

    def split_by_mode(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
    ) -> Dict[str, np.ndarray]:
        """
        Split the DataFrame into per-mode feature arrays.

        Returns:
            {mode_label: X_array_for_that_mode}
        """
        if not self.is_configured() or self.mode_column not in df.columns:
            return {"all": df[feature_cols].values}

        result = {}
        for mode, grp in df.groupby(self.mode_column):
            mode_key = str(mode)
            result[mode_key] = grp[feature_cols].values
            print(f"[ModeDetector] Mode '{mode_key}': {len(grp)} training rows.")
        return result

    def get_mode_for_row(
        self,
        row: pd.Series,
    ) -> Optional[str]:
        """Return the operating mode for a single inference row."""
        if not self.is_configured():
            return None
        return str(row.get(self.mode_column, "unknown"))

    def is_unknown_mode(self, mode_label: str) -> bool:
        """Return True if a mode label has not been seen during training."""
        return mode_label not in self.known_modes

    def apply_mode_threshold(
        self,
        score: float,
        mode_label: str,
        global_threshold: float,
    ) -> Tuple[bool, float]:
        """
        Apply the correct threshold for the given mode.
        Falls back to global_threshold if no per-mode threshold is stored.

        Returns:
            (is_anomaly, applied_threshold)
        """
        threshold = self.mode_thresholds.get(mode_label, global_threshold)
        return float(score) > threshold, threshold

    def register_mode_thresholds(self, mode_thresholds: Dict[str, float]) -> None:
        """Store calibrated per-mode thresholds after calibration."""
        self.mode_thresholds = mode_thresholds
        print(f"[ModeDetector] Registered thresholds for {len(mode_thresholds)} modes.")

    def evaluate_per_mode(
        self,
        df_eval: pd.DataFrame,
        scores: np.ndarray,
        y_true: Optional[np.ndarray],
        global_threshold: float,
        feature_cols: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute per-mode anomaly rate and threshold usage.
        """
        if not self.is_configured() or self.mode_column not in df_eval.columns:
            return {}

        results = {}
        for mode, grp_idx in df_eval.groupby(self.mode_column).groups.items():
            idx = grp_idx.tolist()
            mode_scores = scores[idx]
            threshold = self.mode_thresholds.get(str(mode), global_threshold)
            preds = (mode_scores > threshold).astype(int)
            results[str(mode)] = {
                "n_samples": len(idx),
                "threshold_used": threshold,
                "pct_flagged": round(float(preds.mean()), 4),
            }
        return results
