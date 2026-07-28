"""
drift.py — RegressionDriftPolicy: monitor and trigger retraining
================================================================
Signal: RMSE on holdout set increases beyond a threshold %.
Action: Log drift, flag manifest status as "drift_detected", triggering retrain.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.metrics import root_mean_squared_error


def check_regression_drift(
    model: Any,
    X_new: np.ndarray,
    y_new: np.ndarray,
    baseline_rmse: float,
    manifest: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Compare current RMSE on new production data against baseline training RMSE.
    Triggers a retrain flag if degradation exceeds the configured threshold.

    Args:
        model:          Trained model in production.
        X_new:          New incoming feature batch.
        y_new:          Ground truth labels for new batch (must be available).
        baseline_rmse:  RMSE from the original validation set.
        manifest:       Pipeline manifest with drift_policy configuration.

    Returns:
        (drift_detected, drift_report)
    """
    drift_cfg = manifest.get("drift_policy", {}).get("regression_drift", {})
    threshold_pct = float(drift_cfg.get("trigger_threshold_rmse_increase_pct", 20.0))

    y_pred = model.predict(X_new)
    current_rmse = float(root_mean_squared_error(y_new, y_pred))
    pct_increase = (current_rmse - baseline_rmse) / max(baseline_rmse, 1e-8) * 100

    drift_detected = pct_increase > threshold_pct

    report = {
        "baseline_rmse": round(baseline_rmse, 4),
        "current_rmse": round(current_rmse, 4),
        "pct_increase": round(pct_increase, 2),
        "threshold_pct": threshold_pct,
        "drift_detected": drift_detected,
        "recommended_action": "retrain" if drift_detected else "monitor",
    }

    if drift_detected:
        print(f"[RegressionDrift] ⚠️  Performance degraded by {pct_increase:.1f}% "
              f"(RMSE: {baseline_rmse:.4f} → {current_rmse:.4f}). Triggering RETRAIN.")
        manifest["status"] = "drift_detected_retrain_required"
    else:
        print(f"[RegressionDrift] ✅ No significant drift. RMSE change: {pct_increase:.1f}%")

    manifest.setdefault("monitoring", {})
    manifest["monitoring"]["regression_drift"] = report
    return drift_detected, report


class RegressionDriftPolicy:
    """
    Class-based wrapper around check_regression_drift for scenario testing
    and for use in the monitoring pipeline when ground-truth labels are available
    on a holdout window.

    Usage:
        policy = RegressionDriftPolicy(manifest)
        action, report = policy.evaluate(baseline_rmse=10.0, current_rmse=14.0)
    """

    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest
        drift_cfg = manifest.get("drift_policy", {}).get("regression_drift", {})
        self.threshold_pct = float(drift_cfg.get("trigger_threshold_rmse_increase_pct", 20.0))
        self.action_on_drift = drift_cfg.get("action", "retrain")

    def evaluate(
        self,
        baseline_rmse: float,
        current_rmse: float,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Compare two RMSE values and return the recommended drift action.

        Returns:
            action: "retrain" | "none"
            report: dict with rmse values, increase %, and decision
        """
        pct_increase = (current_rmse - baseline_rmse) / max(baseline_rmse, 1e-8) * 100
        drift_detected = pct_increase > self.threshold_pct

        action = self.action_on_drift if drift_detected else "none"

        report = {
            "baseline_rmse":     round(baseline_rmse, 4),
            "current_rmse":      round(current_rmse, 4),
            "pct_increase":      round(pct_increase, 2),
            "rmse_increase_pct": round(pct_increase, 2),
            "threshold_pct":     self.threshold_pct,
            "drift_detected":    drift_detected,
            "action":            action,
            "recommended_action": action,
        }

        self.manifest.setdefault("monitoring", {})
        self.manifest["monitoring"]["regression_drift"] = report
        return action, report


# ── G-10 Fix: Population Stability Index (PSI) Drift without targets ──────────

def calculate_psi(baseline: np.ndarray, new_batch: np.ndarray, num_bins: int = 10) -> float:
    """Calculate Population Stability Index (PSI) between baseline and new batch."""
    baseline = baseline[~np.isnan(baseline)]
    new_batch = new_batch[~np.isnan(new_batch)]

    if len(baseline) == 0 or len(new_batch) == 0:
        return 0.0

    percentiles = np.linspace(0, 100, num_bins + 1)
    bins = np.percentile(baseline, percentiles)
    bins[0] -= 1e-5
    bins[-1] += 1e-5
    bins = np.unique(bins)

    if len(bins) < 2:
        return 0.0

    base_counts, _ = np.histogram(baseline, bins=bins)
    new_counts, _  = np.histogram(new_batch, bins=bins)

    base_pct = base_counts / max(len(baseline), 1)
    new_pct  = new_counts  / max(len(new_batch), 1)

    base_pct = np.where(base_pct == 0, 1e-4, base_pct)
    new_pct  = np.where(new_pct  == 0, 1e-4, new_pct)

    psi = np.sum((new_pct - base_pct) * np.log(new_pct / base_pct))
    return float(psi)


def check_feature_drift(
    X_baseline: np.ndarray,
    X_new: np.ndarray,
    feature_cols: list[str],
    psi_threshold: float = 0.25,
) -> tuple[bool, dict[str, float]]:
    """
    G-10 Fix: Unsupervised feature drift check (PSI) when y_new is unavailable.
    PSI > 0.25 indicates significant population shift.
    """
    feature_psis = {}
    drifted_features = []

    for i, col in enumerate(feature_cols):
        if i < X_baseline.shape[1] and i < X_new.shape[1]:
            psi = calculate_psi(X_baseline[:, i], X_new[:, i])
            feature_psis[col] = round(psi, 4)
            if psi >= psi_threshold:
                drifted_features.append(col)

    drift_detected = len(drifted_features) > 0
    print(f"[FeatureDrift] Evaluated PSI across {len(feature_cols)} features. "
          f"Drifted features: {len(drifted_features)} (threshold={psi_threshold})")

    report = {
        "drift_detected": drift_detected,
        "psi_threshold": psi_threshold,
        "drifted_features": drifted_features,
        "feature_psis": feature_psis,
    }
    return drift_detected, report
