"""
quality_checks.py — Data quality detection before modeling
===========================================================
Runs pre-modeling checks that catch bad data patterns before they
silently corrupt the trained model.

Checks performed:
  1. Stuck/flatlined sensor detection (zero variance over N consecutive rows)
  2. High null rate per column
  3. Duplicate row detection
  4. Sensor value range violations (if bounds defined in manifest)
  5. Timestamp continuity check (monotonic, no backwards jumps)
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np


def detect_stuck_sensors(
    df: pd.DataFrame,
    window: int = 20,
    variance_threshold: float = 1e-8,
) -> List[str]:
    """
    Detect sensors that have zero (or near-zero) variance over a rolling window.
    These are either broken sensors or constant-valued data columns.

    Returns:
        List of column names flagged as stuck/degenerate.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stuck = []
    for col in numeric_cols:
        rolling_var = df[col].rolling(window=window, min_periods=window).var()
        stuck_fraction = (rolling_var < variance_threshold).mean()
        if stuck_fraction > 0.5:  # >50% of windows are flat
            stuck.append(col)
    return stuck


def check_null_rates(
    df: pd.DataFrame,
    threshold: float = 0.30,
) -> Dict[str, float]:
    """
    Compute null rate per column. Flag columns exceeding the threshold.

    Returns:
        Dict of {col: null_rate} for columns above the threshold.
    """
    null_rates = df.isnull().mean()
    return {col: float(rate) for col, rate in null_rates.items() if rate > threshold}


def detect_duplicates(df: pd.DataFrame) -> Tuple[int, float]:
    """
    Count duplicate rows.

    Returns:
        (duplicate_count, duplicate_fraction)
    """
    n_dupes = int(df.duplicated().sum())
    fraction = n_dupes / max(len(df), 1)
    return n_dupes, fraction


def check_sensor_bounds(
    df: pd.DataFrame,
    bounds: Dict[str, Dict[str, float]],
) -> Dict[str, Dict[str, Any]]:
    """
    Check if sensor values fall within declared bounds from the manifest.

    Args:
        df:     DataFrame with sensor columns.
        bounds: {column: {"min": v, "max": v}} dict from manifest schema config.

    Returns:
        Dict of {col: {"violation_count": int, "violation_fraction": float}}
        for columns with violations.
    """
    violations = {}
    for col, limits in bounds.items():
        if col not in df.columns:
            continue
        lo = limits.get("min", -np.inf)
        hi = limits.get("max", np.inf)
        mask = (df[col] < lo) | (df[col] > hi)
        n_violations = int(mask.sum())
        if n_violations > 0:
            violations[col] = {
                "violation_count": n_violations,
                "violation_fraction": round(n_violations / len(df), 4),
            }
    return violations


def check_timestamp_monotonicity(
    df: pd.DataFrame,
    timestamp_col: str,
) -> Dict[str, Any]:
    """
    Verify that timestamps are strictly increasing (no backwards jumps).

    Returns:
        {"is_monotonic": bool, "n_violations": int}
    """
    if timestamp_col not in df.columns:
        return {"is_monotonic": True, "n_violations": 0}
    ts = pd.to_datetime(df[timestamp_col])
    diffs = ts.diff().dropna()
    n_violations = int((diffs <= pd.Timedelta(0)).sum())
    return {"is_monotonic": n_violations == 0, "n_violations": n_violations}


def run_quality_checks(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Pipeline entry point. Runs all quality checks and returns:
      - Cleaned DataFrame (duplicates removed)
      - Updated manifest with quality_report
      - quality_report dict (used by VG_1 gate)
    """
    print("[QualityChecks] Running data quality scan...")
    report: Dict[str, Any] = {}

    # 1. Stuck sensors
    stuck = detect_stuck_sensors(df)
    report["stuck_sensors"] = stuck
    if stuck:
        print(f"[QualityChecks] ⚠️  Stuck/flatlined sensors detected: {stuck}")

    # 2. High null rates
    high_null_cols = check_null_rates(df, threshold=0.30)
    report["high_null_columns"] = high_null_cols
    if high_null_cols:
        print(f"[QualityChecks] ⚠️  High null rate (>30%) columns: {list(high_null_cols.keys())}")

    # 3. Duplicates
    n_dupes, dupe_fraction = detect_duplicates(df)
    report["duplicate_rows"] = n_dupes
    report["duplicate_fraction"] = round(dupe_fraction, 4)
    if n_dupes > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        print(f"[QualityChecks] Removed {n_dupes} duplicate rows ({dupe_fraction:.1%}).")

    # 4. Sensor bounds (if declared)
    bounds = manifest.get("schema_config", {}).get("sensor_bounds", {})
    if bounds:
        violations = check_sensor_bounds(df, bounds)
        report["sensor_bound_violations"] = violations
        if violations:
            print(f"[QualityChecks] ⚠️  Sensor bound violations in: {list(violations.keys())}")

    # 5. Timestamp monotonicity
    ts_col = manifest.get("schema_config", {}).get("timestamp_column")
    if ts_col and ts_col in df.columns:
        ts_report = check_timestamp_monotonicity(df, ts_col)
        report["timestamp_monotonicity"] = ts_report
        if not ts_report["is_monotonic"]:
            print(f"[QualityChecks] ⚠️  Timestamp non-monotonic: {ts_report['n_violations']} violations.")

    manifest.setdefault("data_info", {})
    manifest["data_info"]["quality_report"] = report
    manifest["data_info"]["post_dedup_rows"] = int(len(df))

    print(f"[QualityChecks] Complete. Shape after dedup: {df.shape}")
    return df, manifest, report
