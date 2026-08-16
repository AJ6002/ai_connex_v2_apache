"""
threshold.py — ThresholdCalibrator: anomaly alarm sensitivity tuning
=====================================================================
Every anomaly model outputs a raw score. This module converts that score
into a binary "anomaly / not anomaly" decision by calibrating a threshold.

Three calibration strategies:
  percentile   → set at Nth percentile of validation scores (e.g. 99th)
  cost_based   → minimize (false_alarm_cost + missed_detection_cost)
  sme_override → use a fixed value from a domain expert

Also supports per-operating-mode threshold calibration when multiple
legitimate operating regimes are present.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
import numpy as np


class ThresholdCalibrator:
    """
    Calibrates the anomaly decision threshold from validation-set scores.

    Usage:
        calibrator = ThresholdCalibrator(manifest)
        threshold, report = calibrator.calibrate(val_scores, y_val_true=None)
    """

    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest
        threshold_cfg = manifest.get("threshold_config", {})
        self.method = threshold_cfg.get("method", "percentile")
        self.percentile = float(threshold_cfg.get("percentile", 99.0))
        self.sme_threshold = threshold_cfg.get("sme_override_threshold")
        self.max_far_per_week = threshold_cfg.get("max_false_alarm_rate_per_week")
        self.threshold: Optional[float] = None

    def calibrate(
        self,
        val_scores: np.ndarray,
        y_val_true: Optional[np.ndarray] = None,
        false_alarm_cost: float = 100.0,
        miss_cost: float = 10000.0,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calibrate the threshold using the configured method.

        Args:
            val_scores:        Anomaly scores on validation set (higher = more anomalous).
            y_val_true:        True binary labels (1=anomaly, 0=normal). Optional.
            false_alarm_cost:  Cost of one false positive alarm.
            miss_cost:         Cost of one missed true anomaly.

        Returns:
            (threshold, calibration_report)
        """
        if self.method == "sme_override" and self.sme_threshold is not None:
            self.threshold = float(self.sme_threshold)
            report = {
                "method": "sme_override",
                "threshold": self.threshold,
                "note": "Domain-expert defined fixed threshold.",
            }

        elif self.method == "cost_based" and y_val_true is not None:
            self.threshold, report = self._cost_based_calibration(
                val_scores, y_val_true, false_alarm_cost, miss_cost
            )

        else:
            # Default: percentile
            self.threshold = float(np.percentile(val_scores, self.percentile))
            # Estimate false alarm rate on validation set
            far_estimate = float((val_scores > self.threshold).mean())
            report = {
                "method": "percentile",
                "percentile": self.percentile,
                "threshold": round(self.threshold, 6),
                "estimated_far_on_val": round(far_estimate, 4),
            }

        print(f"[ThresholdCalibrator] Method='{report['method']}' → Threshold={self.threshold:.6f}")
        if report.get("estimated_far_on_val") is not None:
            weekly_far = report["estimated_far_on_val"] * 7 * 24 * 6  # ~10-min intervals
            print(f"[ThresholdCalibrator] Estimated false alarm rate: "
                  f"{report['estimated_far_on_val']:.2%} (~{weekly_far:.0f}/week)")

        self.manifest.setdefault("results", {})
        self.manifest["results"]["threshold_calibration"] = report
        return self.threshold, report

    def calibrate_per_mode(
        self,
        val_scores: np.ndarray,
        val_modes: np.ndarray,
    ) -> Dict[str, float]:
        """
        Calibrate a separate threshold for each operating mode.
        Returns {mode_label: threshold_value}.
        """
        mode_thresholds: Dict[str, float] = {}
        for mode in np.unique(val_modes):
            mask = val_modes == mode
            mode_scores = val_scores[mask]
            if len(mode_scores) < 10:
                print(f"[ThresholdCalibrator] Mode '{mode}': too few samples ({len(mode_scores)}). Skipping.")
                continue
            t = float(np.percentile(mode_scores, self.percentile))
            mode_thresholds[str(mode)] = round(t, 6)
            print(f"[ThresholdCalibrator] Mode '{mode}' threshold={t:.6f}")

        self.manifest.setdefault("results", {})
        self.manifest["results"]["per_mode_thresholds"] = mode_thresholds
        return mode_thresholds

    def _cost_based_calibration(
        self,
        scores: np.ndarray,
        y_true: np.ndarray,
        fa_cost: float,
        miss_cost: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Sweep threshold values and find the one that minimizes total business cost.
        """
        candidates = np.percentile(scores, np.arange(80, 99.9, 0.5))
        best_threshold = candidates[0]
        best_cost = float("inf")

        for t in candidates:
            preds = (scores > t).astype(int)
            fp = int(((preds == 1) & (y_true == 0)).sum())
            fn = int(((preds == 0) & (y_true == 1)).sum())
            total_cost = fp * fa_cost + fn * miss_cost
            if total_cost < best_cost:
                best_cost = total_cost
                best_threshold = t

        report = {
            "method": "cost_based",
            "threshold": round(float(best_threshold), 6),
            "minimum_total_cost": round(best_cost, 2),
            "false_alarm_cost_per_event": fa_cost,
            "miss_detection_cost_per_event": miss_cost,
        }
        return float(best_threshold), report

    def predict(self, scores: np.ndarray) -> np.ndarray:
        """Apply the calibrated threshold to produce binary predictions."""
        if self.threshold is None:
            raise RuntimeError("Threshold not calibrated. Call calibrate() first.")
        return (scores > self.threshold).astype(int)
