"""
time_alignment.py — Multi-rate sensor resampling and clock alignment
=====================================================================
Industrial sensors write data at different rates (e.g., temp every 1s,
flow every 5s, lab test every 4 hours). This module resamples all streams
to a common clock interval and detects/logs data gaps.

Key operations:
  - Resample to common interval (forward-fill, mean aggregation, or interpolation)
  - Detect and log time gaps larger than a threshold
  - Align multi-entity datasets (one entity at a time)
  - Apply label lag: shift target column backwards by known lab delay
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np


def align_to_common_clock(
    df: pd.DataFrame,
    timestamp_col: str,
    interval: str = "10s",
    agg_method: str = "mean",
    fill_method: str = "ffill",
) -> pd.DataFrame:
    """
    Resample a time-indexed DataFrame to a uniform time interval.

    Args:
        df:             Input DataFrame with a datetime timestamp column.
        timestamp_col:  Name of the timestamp column.
        interval:       Pandas offset string (e.g., '10s', '1min', '5min').
        agg_method:     Aggregation for resampling: 'mean', 'median', 'last'.
        fill_method:    Fill remaining NaNs after resampling: 'ffill', 'bfill', 'linear'.

    Returns:
        Resampled DataFrame with a uniform DatetimeIndex.
    """
    if timestamp_col not in df.columns:
        raise KeyError(f"Timestamp column '{timestamp_col}' not found in DataFrame.")

    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df = df.set_index(timestamp_col).sort_index()

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    # Resample numeric columns
    if agg_method == "mean":
        resampled = df[numeric_cols].resample(interval).mean()
    elif agg_method == "median":
        resampled = df[numeric_cols].resample(interval).median()
    elif agg_method == "last":
        resampled = df[numeric_cols].resample(interval).last()
    else:
        raise ValueError(f"Unsupported agg_method: '{agg_method}'")

    # Forward-fill categorical columns using last observation
    if cat_cols:
        cat_resampled = df[cat_cols].resample(interval).last()
        resampled = pd.concat([resampled, cat_resampled], axis=1)

    # Fill remaining NaN values
    if fill_method == "ffill":
        resampled = resampled.ffill()
    elif fill_method == "bfill":
        resampled = resampled.bfill()
    elif fill_method == "linear":
        resampled[numeric_cols] = resampled[numeric_cols].interpolate(method="linear")
        resampled[cat_cols] = resampled[cat_cols].ffill()

    return resampled.reset_index()


def detect_gaps(
    df: pd.DataFrame,
    timestamp_col: str,
    expected_interval: str,
    gap_multiplier: float = 3.0,
) -> List[Dict[str, Any]]:
    """
    Detect gaps in the time series that exceed gap_multiplier * expected_interval.

    Returns a list of gap records: [{"start": t1, "end": t2, "duration_seconds": n}, ...]
    """
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df = df.sort_values(timestamp_col)

    expected_delta = pd.tseries.frequencies.to_offset(expected_interval)
    expected_seconds = pd.Timedelta(expected_delta).total_seconds()
    threshold_seconds = expected_seconds * gap_multiplier

    diffs = df[timestamp_col].diff()
    gaps = []
    for i, delta in enumerate(diffs):
        if pd.notna(delta) and delta.total_seconds() > threshold_seconds:
            gaps.append({
                "start": str(df[timestamp_col].iloc[i - 1]),
                "end": str(df[timestamp_col].iloc[i]),
                "duration_seconds": delta.total_seconds(),
            })
    return gaps


def apply_label_lag(
    df: pd.DataFrame,
    target_col: str,
    lag_seconds: int,
    timestamp_col: str,
    entity_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Shift the target column backward by `lag_seconds` to correct for
    known lab result delays (e.g., quality test results arrive 4h later).

    Example: if lag_seconds=14400 (4h), the target at row T corresponds
    to the sensor features at row T-4h.
    """
    if lag_seconds == 0:
        return df

    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    df = df.sort_values(timestamp_col)

    lag = pd.Timedelta(seconds=lag_seconds)
    df["_align_time"] = df[timestamp_col] - lag

    by_param = entity_col if (entity_col and entity_col in df.columns) else None
    target_subset_cols = [timestamp_col, target_col] + ([entity_col] if by_param else [])

    aligned = pd.merge_asof(
        df.drop(columns=[target_col]).rename(columns={timestamp_col: "_sensor_time"}),
        df[target_subset_cols].rename(columns={timestamp_col: "_align_time"}),
        on="_align_time",
        by=by_param,
        direction="nearest",
    )
    aligned = aligned.rename(columns={"_sensor_time": timestamp_col})
    aligned = aligned.drop(columns=["_align_time"])
    print(f"[TimeAlignment] Applied entity-aware label lag: {lag_seconds}s on '{target_col}' (entity='{by_param}')")
    return aligned


def run_time_alignment(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Pipeline entry point. Reads alignment config from manifest and runs alignment.
    Only executes if data_topology is 'time_series' or 'multi_entity_time_series'.
    """
    topology = manifest.get("data_topology", "tabular")
    if topology == "tabular":
        print("[TimeAlignment] Tabular data — skipping time alignment.")
        return df, manifest

    timestamp_col = manifest.get("schema_config", {}).get("timestamp_column")
    entity_col = manifest.get("schema_config", {}).get("entity_column")
    if not timestamp_col:
        print("[TimeAlignment] No timestamp_column set — skipping.")
        return df, manifest

    prep_recipe = manifest.get("recipes", {}).get("preparing", {})
    interval = prep_recipe.get("time_align", {}).get("interval_seconds", 10)
    interval_str = f"{interval}s"

    print(f"[TimeAlignment] Resampling to {interval_str} clock interval...")
    df = align_to_common_clock(df, timestamp_col, interval=interval_str)

    # Detect gaps and log
    gaps = detect_gaps(df, timestamp_col, expected_interval=interval_str)
    manifest.setdefault("data_info", {})
    manifest["data_info"]["detected_gaps"] = len(gaps)
    if gaps:
        print(f"[TimeAlignment] ⚠️  Detected {len(gaps)} time gaps exceeding 3x expected interval.")
        manifest["data_info"]["gap_details"] = gaps[:10]  # log first 10

    # Apply label lag if configured
    label_contract = manifest.get("label_contract", {})
    lag_seconds = label_contract.get("label_lag_seconds", 0) or manifest.get("label_lag_seconds", 0)
    target_col = label_contract.get("target_column") or manifest.get("target_column")
    if lag_seconds and target_col and target_col in df.columns:
        df = apply_label_lag(df, target_col, lag_seconds, timestamp_col, entity_col=entity_col)

    print(f"[TimeAlignment] Aligned shape: {df.shape}")
    return df, manifest
