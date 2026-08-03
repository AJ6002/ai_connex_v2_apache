"""
drift.py — AnomalyDriftPolicy: two-path drift response (recalibrate vs retrain)
================================================================================
Unlike regression (always retrain), anomaly drift has two distinct responses:

  Path 1 — Score distribution shifted, features stable:
    → Auto-recalibrate threshold only (fast, cheap, no new model needed)

  Path 2 — Feature distribution shifted (true concept drift):
    → Trigger retrain of the normal-state model (expensive, requires approval)

Both paths are detected using PSI (Population Stability Index) and KS-test.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple
import numpy as np
from scipy import stats


def compute_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Compute Population Stability Index between two distributions."""
    breakpoints = np.histogram_bin_edges(expected, bins=bins)
    exp_counts, _ = np.histogram(expected, bins=breakpoints)
    act_counts, _ = np.histogram(actual, bins=breakpoints)
    exp_pct = exp_counts / max(exp_counts.sum(), 1)
    act_pct = act_counts / max(act_counts.sum(), 1)
    exp_pct = np.where(exp_pct == 0, 1e-6, exp_pct)
    act_pct = np.where(act_pct == 0, 1e-6, act_pct)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def run_ks_test(baseline: np.ndarray, current: np.ndarray) -> Tuple[float, float]:
    """Run KS-test. Returns (ks_statistic, p_value)."""
    result = stats.ks_2samp(baseline, current)
    return float(result.statistic), float(result.pvalue)


class AnomalyDriftPolicy:
    """
    Drift detection and response policy for anomaly detection models.

    Usage:
        policy = AnomalyDriftPolicy(manifest)
        action, report = policy.evaluate(
            baseline_scores, current_scores,
            baseline_features, current_features
        )
    """

    def __init__(self, manifest: Dict[str, Any]):
        drift_cfg = manifest.get("drift_policy", {}).get("anomaly_drift", {})
        self.psi_threshold = float(drift_cfg.get("psi_threshold", 0.2))
        action_routing = drift_cfg.get("action_routing", {})
        self.score_drift_action = action_routing.get(
            "score_distribution_shifted_only", "recalibrate_threshold"
        )
        self.feature_drift_action = action_routing.get(
            "feature_distribution_shifted", "retrain_normal_model"
        )
        self.manifest = manifest

    def evaluate(
        self,
        baseline_scores: np.ndarray,
        current_scores: np.ndarray,
        baseline_features: np.ndarray,
        current_features: np.ndarray,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Evaluate drift in both score and feature distributions.
        Returns the recommended action and a detailed report.

        Returns:
            action: "none" | "recalibrate_threshold" | "retrain_normal_model"
            report: Dict with PSI values, KS statistics, and decision rationale.
        """
        # Score distribution drift
        score_psi = compute_psi(baseline_scores, current_scores)
        score_ks, score_ks_pval = run_ks_test(baseline_scores, current_scores)

        # Feature distribution drift (average PSI across all features)
        feature_psis = []
        for i in range(baseline_features.shape[1]):
            col_psi = compute_psi(baseline_features[:, i], current_features[:, i])
            feature_psis.append(col_psi)
        mean_feature_psi = float(np.mean(feature_psis))

        score_drifted = score_psi > self.psi_threshold
        features_drifted = mean_feature_psi > self.psi_threshold

        report = {
            "score_psi": round(score_psi, 4),
            "score_ks_statistic": round(score_ks, 4),
            "score_ks_pvalue": round(score_ks_pval, 4),
            "mean_feature_psi": round(mean_feature_psi, 4),
            "score_drifted": score_drifted,
            "features_drifted": features_drifted,
            "psi_threshold": self.psi_threshold,
        }

        if features_drifted:
            action = self.feature_drift_action  # "retrain_normal_model"
            report["decision"] = (
                f"Feature distribution shifted (PSI={mean_feature_psi:.3f} > {self.psi_threshold}). "
                f"Action: {action}."
            )
        elif score_drifted:
            action = self.score_drift_action  # "recalibrate_threshold"
            report["decision"] = (
                f"Score distribution shifted (PSI={score_psi:.3f}) but features stable. "
                f"Action: {action}."
            )
        else:
            action = "none"
            report["decision"] = "No significant drift detected. No action required."

        report["recommended_action"] = action

        print(f"[AnomalyDrift] Score PSI={score_psi:.3f} | Feature PSI={mean_feature_psi:.3f}")
        print(f"[AnomalyDrift] → Action: {action}")

        self.manifest.setdefault("monitoring", {})
        self.manifest["monitoring"]["anomaly_drift"] = report
        return action, report
