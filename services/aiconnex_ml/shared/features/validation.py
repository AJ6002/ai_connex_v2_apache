"""
validation.py — Feature quality validation: leakage, collinearity, PSI drift
=============================================================================
Runs post-engineering checks before training begins.
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd


def check_feature_leakage(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    target_col: str,
    threshold: float = 0.95,
) -> List[str]:
    """
    Detect features that are suspiciously correlated with the target on the test set.
    High test correlation may indicate target leakage (future information bleeding in).

    Returns: List of potentially leaked feature column names.
    """
    if target_col not in df_test.columns:
        return []
    numeric_cols = df_test.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [c for c in numeric_cols if c != target_col]
    target = df_test[target_col]
    leaked = []
    for col in feature_cols:
        corr = abs(df_test[col].corr(target))
        if corr >= threshold:
            leaked.append(col)
    return leaked


def compute_psi(
    expected: pd.Series,
    actual: pd.Series,
    bins: int = 10,
) -> float:
    """
    Compute Population Stability Index (PSI) between expected (train) and
    actual (val/prod) distributions.

    PSI < 0.1  → stable, no action needed
    PSI 0.1-0.2 → minor shift, monitor
    PSI > 0.2  → significant shift, investigate or recalibrate
    """
    expected = expected.dropna()
    actual = actual.dropna()
    breakpoints = np.histogram_bin_edges(expected, bins=bins)
    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)

    # Avoid division by zero
    expected_pct = expected_counts / max(len(expected), 1)
    actual_pct = actual_counts / max(len(actual), 1)
    expected_pct = np.where(expected_pct == 0, 1e-6, expected_pct)
    actual_pct = np.where(actual_pct == 0, 1e-6, actual_pct)

    psi = float(np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct)))
    return round(psi, 4)


def check_high_collinearity(
    df: pd.DataFrame,
    feature_cols: List[str],
    threshold: float = 0.95,
) -> List[Tuple[str, str, float]]:
    """
    Find pairs of features with correlation above threshold.
    Returns: [(col_a, col_b, correlation), ...]
    """
    corr = df[feature_cols].corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    pairs = [
        (col, row, round(float(upper.loc[row, col]), 4))
        for col in upper.columns
        for row in upper.index
        if pd.notna(upper.loc[row, col]) and upper.loc[row, col] >= threshold
    ]
    return pairs


def run_feature_validation(
    df_train: pd.DataFrame,
    df_val: pd.DataFrame,
    feature_cols: List[str],
    target_col: str | None,
    manifest: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run all feature quality checks and return a validation summary dict.
    """
    report: Dict[str, Any] = {}

    # PSI drift (train vs val distribution)
    psi_results = {}
    for col in feature_cols:
        if col in df_train.columns and col in df_val.columns:
            psi_val = compute_psi(df_train[col], df_val[col])
            if psi_val > 0.1:
                psi_results[col] = psi_val
    report["psi_drifted_features"] = psi_results
    if psi_results:
        print(f"[FeatureValidation] PSI shift detected in: {list(psi_results.keys())}")

    # High collinearity
    high_corr = check_high_collinearity(df_train, feature_cols)
    report["high_collinear_pairs"] = [(a, b, c) for a, b, c in high_corr]
    if high_corr:
        print(f"[FeatureValidation] ⚠️  {len(high_corr)} highly correlated feature pairs (>0.95).")

    manifest.setdefault("data_info", {})
    manifest["data_info"]["feature_validation"] = report
    return report
