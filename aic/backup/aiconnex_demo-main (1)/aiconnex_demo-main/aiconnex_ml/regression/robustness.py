"""
robustness.py — Regression robustness stress testing
=====================================================
Injects Gaussian noise and simulates sensor dropout to measure
how much prediction error degrades under realistic industrial conditions.
"""

from __future__ import annotations
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import root_mean_squared_error


def inject_gaussian_noise(
    X: np.ndarray,
    sigma_fraction: float = 0.05,
    random_state: int = 42,
) -> np.ndarray:
    """
    Add Gaussian noise to all features.
    sigma_fraction: noise std as a fraction of each feature's own std.
    """
    rng = np.random.default_rng(random_state)
    feature_stds = X.std(axis=0, keepdims=True)
    noise = rng.normal(0, sigma_fraction * feature_stds, size=X.shape)
    return X + noise


def inject_sensor_dropout(
    X: np.ndarray,
    dropout_fraction: float = 0.1,
    random_state: int = 42,
) -> np.ndarray:
    """
    Simulate sensor failure: set a random fraction of feature values to zero.
    """
    rng = np.random.default_rng(random_state)
    X_corrupted = X.copy().astype(float)
    mask = rng.random(size=X.shape) < dropout_fraction
    X_corrupted[mask] = 0.0
    return X_corrupted


def run_robustness_tests(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    manifest: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run regression robustness stress tests:
      1. Gaussian noise at 5%, 10%, 15%, 20% sigma fractions
      2. Sensor dropout at 10%, 20%, 30% dropout rates

    Checks each against the degradation threshold from quality_gates.

    Returns robustness_report dict and updates manifest.
    """
    base_pred = model.predict(X_test)
    base_rmse = float(root_mean_squared_error(y_test, base_pred))

    max_deg_pct = float(
        manifest.get("quality_gates", {})
        .get("regression_gates", {})
        .get("robustness_noise_degradation_pct", 15.0)
    )

    noise_results = []
    for sigma in [0.05, 0.10, 0.15, 0.20]:
        X_noisy = inject_gaussian_noise(X_test, sigma_fraction=sigma)
        pred = model.predict(X_noisy)
        rmse = float(root_mean_squared_error(y_test, pred))
        deg_pct = (rmse - base_rmse) / max(base_rmse, 1e-8) * 100
        noise_results.append({
            "sigma_fraction": sigma,
            "rmse": round(rmse, 4),
            "degradation_pct": round(deg_pct, 2),
            "passed": deg_pct <= max_deg_pct,
        })
        print(f"[Robustness] Noise σ={sigma:.0%}  RMSE={rmse:.4f}  Δ={deg_pct:+.1f}%"
              + (" ✅" if deg_pct <= max_deg_pct else " ❌"))

    dropout_results = []
    for dr in [0.10, 0.20, 0.30]:
        X_dropped = inject_sensor_dropout(X_test, dropout_fraction=dr)
        pred = model.predict(X_dropped)
        rmse = float(root_mean_squared_error(y_test, pred))
        deg_pct = (rmse - base_rmse) / max(base_rmse, 1e-8) * 100
        dropout_results.append({
            "dropout_fraction": dr,
            "rmse": round(rmse, 4),
            "degradation_pct": round(deg_pct, 2),
            "passed": deg_pct <= max_deg_pct,
        })
        print(f"[Robustness] Dropout {dr:.0%}  RMSE={rmse:.4f}  Δ={deg_pct:+.1f}%"
              + (" ✅" if deg_pct <= max_deg_pct else " ❌"))

    report = {
        "baseline_rmse": round(base_rmse, 4),
        "max_allowed_degradation_pct": max_deg_pct,
        "noise_tests": noise_results,
        "dropout_tests": dropout_results,
        "overall_passed": all(r["passed"] for r in noise_results + dropout_results),
    }

    manifest.setdefault("results", {})
    manifest["results"]["robustness"] = report
    return report
