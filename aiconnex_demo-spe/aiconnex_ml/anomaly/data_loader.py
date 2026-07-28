"""
data_loader.py — Supervision-mode-specific anomaly data loading
================================================================
Each supervision mode requires fundamentally different data:

  supervised     → load (X_train, y_train) with fault labels
  semi_supervised → load only X_normal (filtered to the healthy normal_period)
  unsupervised   → load X_all (no filtering, no labels)

This module handles all three loading paths.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd


def load_for_supervision_mode(
    df_train: pd.DataFrame,
    feature_cols: list,
    manifest: Dict[str, Any],
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Return (X_train, y_train) appropriate for the supervision_mode.

    For semi_supervised: X_train contains ONLY normal-period rows.
    For unsupervised:    X_train contains all rows, y_train is None.
    For supervised:      X_train contains all rows, y_train contains fault labels.

    Returns:
        X_train: numpy feature array
        y_train: numpy label array (or None for unsupervised/semi_supervised)
    """
    label_cfg = manifest.get("label_contract", {})
    supervision_mode = label_cfg.get("supervision_mode", "unsupervised")

    if supervision_mode == "supervised":
        fault_col = label_cfg.get("fault_label_column")
        if not fault_col or fault_col not in df_train.columns:
            raise ValueError(f"Supervised anomaly requires fault_label_column. "
                             f"Column '{fault_col}' not found.")
        X = df_train[feature_cols].values
        y = df_train[fault_col].values
        n_faults = int((y != 0).sum())
        print(f"[AnomalyLoader] Supervised: {len(X)} rows, {n_faults} fault samples.")
        return X, y

    elif supervision_mode == "semi_supervised":
        normal_period = label_cfg.get("normal_period", {})
        df_normal = _filter_normal_period(df_train, normal_period, manifest)
        X = df_normal[feature_cols].values
        print(f"[AnomalyLoader] Semi-supervised: {len(X)} normal-period rows for training.")
        return X, None

    elif supervision_mode == "unsupervised":
        X = df_train[feature_cols].values
        print(f"[AnomalyLoader] Unsupervised: {len(X)} rows (all data, no labels).")
        return X, None

    else:
        raise ValueError(f"Unknown supervision_mode: '{supervision_mode}'")


def _filter_normal_period(
    df: pd.DataFrame,
    normal_period: Dict[str, Any],
    manifest: Dict[str, Any],
) -> pd.DataFrame:
    """
    Filter DataFrame to retain only the defined normal operating period.

    Supports two filter strategies:
      1. Time-range: {"start": "2026-01-01", "end": "2026-03-15"}
      2. Column-filter: {"filter_column": "is_normal", "filter_value": 1}
    """
    ts_col = manifest.get("schema_config", {}).get("timestamp_column")
    start = normal_period.get("start")
    end = normal_period.get("end")
    filter_col = normal_period.get("filter_column")
    filter_val = normal_period.get("filter_value")

    df_normal = df.copy()

    if start and end and ts_col and ts_col in df.columns:
        df_normal[ts_col] = pd.to_datetime(df_normal[ts_col])
        df_normal = df_normal[
            (df_normal[ts_col] >= pd.Timestamp(start)) &
            (df_normal[ts_col] <= pd.Timestamp(end))
        ]
        print(f"[AnomalyLoader] Normal period filter: {start} → {end}: {len(df_normal)} rows.")

    elif filter_col and filter_col in df.columns:
        df_normal = df_normal[df_normal[filter_col] == filter_val]
        print(f"[AnomalyLoader] Normal period filter: {filter_col}=={filter_val}: {len(df_normal)} rows.")

    if len(df_normal) == 0:
        raise ValueError(
            "Normal period filter returned 0 rows. "
            "Check label_contract.normal_period configuration."
        )

    return df_normal.reset_index(drop=True)
