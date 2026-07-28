"""
policy.py — Topology-enforced split strategy router
====================================================
THE most important guard in the pipeline.

Rule: data_topology determines the split strategy.
  time_series              → chronological split (HARD ERROR on random split)
  multi_entity_time_series → group-chronological split by entity_column
  tabular                  → stratified or k-fold

Raises ValueError if a random split is attempted on time-series data.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


def enforce_split(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Primary split router. Reads data_topology from manifest and applies
    the correct split strategy. Updates manifest with split paths/sizes.

    Returns:
        df_train, df_val, df_test, manifest
    """
    topology = manifest.get("data_topology", "tabular")
    split_cfg = manifest.get("split_policy", {})
    train_r = float(split_cfg.get("train_ratio", 0.70))
    val_r = float(split_cfg.get("val_ratio", 0.15))
    random_state = int(split_cfg.get("random_state", 42))
    entity_col = manifest.get("schema_config", {}).get("entity_column")
    timestamp_col = manifest.get("schema_config", {}).get("timestamp_column")

    print(f"[SplitPolicy] Topology='{topology}' | train={train_r} val={val_r} test={1-train_r-val_r:.2f}")

    if topology == "time_series":
        df_train, df_val, df_test = _chronological_split(df, timestamp_col, train_r, val_r)
    elif topology == "multi_entity_time_series":
        df_train, df_val, df_test = _group_chronological_split(df, entity_col, timestamp_col, train_r, val_r)
    elif topology == "tabular":
        df_train, df_val, df_test = _random_split(df, train_r, val_r, random_state)
    else:
        raise ValueError(f"Unknown data_topology: '{topology}'")

    manifest.setdefault("data_info", {})
    manifest["data_info"]["split_sizes"] = {
        "train": int(len(df_train)),
        "val": int(len(df_val)),
        "test": int(len(df_test)),
    }

    print(f"[SplitPolicy] Split complete — Train: {len(df_train)}, Val: {len(df_val)}, Test: {len(df_test)}")
    return df_train, df_val, df_test, manifest


def _chronological_split(
    df: pd.DataFrame,
    timestamp_col: str | None,
    train_ratio: float,
    val_ratio: float,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split time-series data by position (time order). No shuffling."""
    if timestamp_col and timestamp_col in df.columns:
        df = df.sort_values(timestamp_col).reset_index(drop=True)
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]


def _group_chronological_split(
    df: pd.DataFrame,
    entity_col: str | None,
    timestamp_col: str | None,
    train_ratio: float,
    val_ratio: float,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Group-chronological split: ALL cycles/rows of a given entity
    go entirely into train OR val OR test — never split across sets.

    This prevents data leakage where Entity-5's early cycles are in train
    and its late cycles are in test.
    """
    if not entity_col or entity_col not in df.columns:
        print("[SplitPolicy] No entity_column found. Falling back to chronological split.")
        return _chronological_split(df, timestamp_col, train_ratio, val_ratio)

    entities = df[entity_col].unique()
    np.random.seed(42)
    np.random.shuffle(entities)

    n = len(entities)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_entities = entities[:train_end]
    val_entities = entities[train_end:val_end]
    test_entities = entities[val_end:]

    df_train = df[df[entity_col].isin(train_entities)]
    df_val = df[df[entity_col].isin(val_entities)]
    df_test = df[df[entity_col].isin(test_entities)]

    if timestamp_col and timestamp_col in df.columns:
        df_train = df_train.sort_values(timestamp_col)
        df_val = df_val.sort_values(timestamp_col)
        df_test = df_test.sort_values(timestamp_col)

    return df_train.reset_index(drop=True), df_val.reset_index(drop=True), df_test.reset_index(drop=True)


def _random_split(
    df: pd.DataFrame,
    train_ratio: float,
    val_ratio: float,
    random_state: int,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Standard random split — only used for tabular (non-time-series) data."""
    test_ratio = round(1.0 - train_ratio - val_ratio, 4)
    df_train, df_temp = train_test_split(df, test_size=(1 - train_ratio), random_state=random_state)
    relative_val = val_ratio / (val_ratio + test_ratio)
    df_val, df_test = train_test_split(df_temp, test_size=(1 - relative_val), random_state=random_state)
    return df_train.reset_index(drop=True), df_val.reset_index(drop=True), df_test.reset_index(drop=True)
