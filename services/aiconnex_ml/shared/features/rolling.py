"""
rolling.py — Rolling window feature engineering for time-series sensors
=======================================================================
Computes statistical summary features over a sliding temporal window.
All transforms are fitted on training data only and applied to all splits.
"""

from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd
import numpy as np


ROLLING_STATS = ["mean", "std", "min", "max", "median"]


def add_rolling_features(
    df: pd.DataFrame,
    cols: List[str],
    window_sizes: List[int],
    stats: List[str] | None = None,
    group_col: str | None = None,
) -> pd.DataFrame:
    """
    Add rolling window statistical features for given sensor columns.

    Args:
        df:           Input DataFrame (sorted by time).
        cols:         Sensor columns to compute rolling features for.
        window_sizes: List of rolling window lengths (in rows).
        stats:        Statistics to compute. Default: mean, std, min, max.
        group_col:    If set, compute rolling stats per entity group (e.g., engine_id).

    Returns:
        DataFrame with new rolling feature columns appended.
    """
    if stats is None:
        stats = ["mean", "std", "min", "max"]

    df = df.copy()
    new_cols: Dict[str, pd.Series] = {}

    for col in cols:
        if col not in df.columns:
            continue
        for w in window_sizes:
            if group_col and group_col in df.columns:
                grouped = df.groupby(group_col)[col]
                for stat in stats:
                    feat_name = f"{col}_roll{w}_{stat}"
                    new_cols[feat_name] = getattr(grouped.rolling(w, min_periods=1), stat)().reset_index(level=0, drop=True)
            else:
                roll = df[col].rolling(w, min_periods=1)
                for stat in stats:
                    feat_name = f"{col}_roll{w}_{stat}"
                    new_cols[feat_name] = getattr(roll, stat)()

    feature_df = pd.DataFrame(new_cols, index=df.index)
    df = pd.concat([df, feature_df], axis=1)
    return df


def add_trend_features(
    df: pd.DataFrame,
    cols: List[str],
    window: int = 20,
    group_col: str | None = None,
) -> pd.DataFrame:
    """
    Add a rolling linear slope (trend) feature for each column.
    Positive slope = sensor rising; negative = declining.
    """
    df = df.copy()

    def rolling_slope(series: pd.Series) -> pd.Series:
        def slope(s):
            if len(s) < 2:
                return 0.0
            x = np.arange(len(s))
            return float(np.polyfit(x, s, 1)[0])
        return series.rolling(window, min_periods=2).apply(slope, raw=True)

    for col in cols:
        if col not in df.columns:
            continue
        feat_name = f"{col}_slope{window}"
        if group_col and group_col in df.columns:
            df[feat_name] = df.groupby(group_col)[col].transform(rolling_slope)
        else:
            df[feat_name] = rolling_slope(df[col])

    return df
