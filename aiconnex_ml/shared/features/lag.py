"""
lag.py — Lag feature engineering (delayed observations)
========================================================
Creates lag features: the value of sensor S at time T-N rows.
Used to give the model access to recent historical context.

Also handles sparse-label alignment for quality measurements
where the lab result arrives hours after the sensor window.
"""

from __future__ import annotations
from typing import List
import pandas as pd


def add_lag_features(
    df: pd.DataFrame,
    cols: List[str],
    lags: List[int],
    group_col: str | None = None,
) -> pd.DataFrame:
    """
    Add lag features for specified columns and lag steps.

    Args:
        df:        Input DataFrame (sorted by time).
        cols:      Columns to create lags for.
        lags:      List of lag steps (e.g., [1, 5, 10] rows).
        group_col: Compute lags within each entity group.

    Returns:
        DataFrame with new lag columns appended.
    """
    df = df.copy()

    for col in cols:
        if col not in df.columns:
            continue
        for lag in lags:
            feat_name = f"{col}_lag{lag}"
            if group_col and group_col in df.columns:
                df[feat_name] = df.groupby(group_col)[col].shift(lag)
            else:
                df[feat_name] = df[col].shift(lag)

    return df


def add_diff_features(
    df: pd.DataFrame,
    cols: List[str],
    periods: List[int] = [1],
    group_col: str | None = None,
) -> pd.DataFrame:
    """
    Add first-order difference features: value(T) - value(T-N).
    Useful for detecting rate-of-change patterns.
    """
    df = df.copy()

    for col in cols:
        if col not in df.columns:
            continue
        for p in periods:
            feat_name = f"{col}_diff{p}"
            if group_col and group_col in df.columns:
                df[feat_name] = df.groupby(group_col)[col].diff(p)
            else:
                df[feat_name] = df[col].diff(p)

    return df
