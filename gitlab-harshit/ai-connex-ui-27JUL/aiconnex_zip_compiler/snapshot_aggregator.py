"""
snapshot_aggregator.py — High-Frequency Telemetry & Snapshot Aggregator
========================================================================
Detects and processes folders/archives containing time-series snapshot CSV files
(e.g., FEMTO bearing dataset with acc_XXXXX.csv files). Extracts time-domain 
and statistical vibration features per snapshot window and computes RUL target.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


def is_snapshot_folder_structure(base_dir: Path) -> bool:
    """Check if directory contains bearing/device subfolders with acc_*.csv snapshot files."""
    for root, dirs, files in os.walk(base_dir):
        acc_files = [f for f in files if f.lower().startswith("acc_") and f.lower().endswith(".csv")]
        if len(acc_files) >= 10:
            return True
    return False


def extract_snapshot_features(filepath: Path) -> Dict[str, float]:
    """Read a single 2,560-row vibration snapshot file and compute 14 statistical features."""
    try:
        df = pd.read_csv(filepath, header=None)
        if df.shape[1] >= 6:
            h_acc = df.iloc[:, 4].values
            v_acc = df.iloc[:, 5].values
        elif df.shape[1] >= 2:
            h_acc = df.iloc[:, -2].values
            v_acc = df.iloc[:, -1].values
        else:
            h_acc = df.iloc[:, 0].values
            v_acc = df.iloc[:, 0].values

        def calc_stats(arr: np.ndarray, prefix: str) -> Dict[str, float]:
            arr_clean = np.nan_to_num(arr, nan=0.0)
            mean_val = float(np.mean(arr_clean))
            std_val = float(np.std(arr_clean))
            rms_val = float(np.sqrt(np.mean(arr_clean**2)))
            peak_val = float(np.max(np.abs(arr_clean)))
            
            # Kurtosis and Skewness
            n = len(arr_clean)
            if std_val > 1e-8 and n > 3:
                norm = (arr_clean - mean_val) / std_val
                kurt_val = float(np.mean(norm**4) - 3.0)
                skew_val = float(np.mean(norm**3))
            else:
                kurt_val = 0.0
                skew_val = 0.0

            crest_val = peak_val / (rms_val + 1e-8)

            return {
                f"{prefix}_mean": round(mean_val, 6),
                f"{prefix}_std": round(std_val, 6),
                f"{prefix}_rms": round(rms_val, 6),
                f"{prefix}_peak": round(peak_val, 6),
                f"{prefix}_kurtosis": round(kurt_val, 6),
                f"{prefix}_skewness": round(skew_val, 6),
                f"{prefix}_crest_factor": round(crest_val, 6),
            }

        feats = {}
        feats.update(calc_stats(h_acc, "h"))
        feats.update(calc_stats(v_acc, "v"))
        return feats
    except Exception as e:
        # Fallback dummy features if parse fails
        return {
            "h_mean": 0.0, "h_std": 0.0, "h_rms": 0.0, "h_peak": 0.0, "h_kurtosis": 0.0, "h_skewness": 0.0, "h_crest_factor": 0.0,
            "v_mean": 0.0, "v_std": 0.0, "v_rms": 0.0, "v_peak": 0.0, "v_kurtosis": 0.0, "v_skewness": 0.0, "v_crest_factor": 0.0,
        }


def process_snapshot_dataset(base_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Scans base_dir for Learning_set and Full_Test_Set subdirectories or bearing subfolders,
    aggregates snapshot files into clean tabular DataFrames with RUL targets.
    """
    merged_dfs: Dict[str, pd.DataFrame] = {}

    # Locate Learning_set and Full_Test_Set
    learning_dir = None
    test_dir = None

    for root, dirs, files in os.walk(base_dir):
        for d in dirs:
            if d.lower() in ("learning_set", "train", "training_set"):
                learning_dir = Path(root) / d
            elif d.lower() in ("full_test_set", "test", "test_set"):
                test_dir = Path(root) / d

    if not learning_dir:
        learning_dir = base_dir

    # 1. Process Learning Set (Training Bearings)
    train_rows = []
    bearing_dirs = [d for d in learning_dir.iterdir() if d.is_dir() and "bearing" in d.name.lower()]
    if not bearing_dirs:
        bearing_dirs = [d for d in learning_dir.glob("*") if d.is_dir()]

    for bdir in sorted(bearing_dirs):
        bearing_id = bdir.name
        acc_files = sorted(
            [f for f in bdir.glob("acc_*.csv")],
            key=lambda p: int(re.search(r"\d+", p.name).group()) if re.search(r"\d+", p.name) else 0
        )
        if not acc_files:
            continue

        total_snapshots = len(acc_files)
        for idx, fpath in enumerate(acc_files, start=1):
            feats = extract_snapshot_features(fpath)
            # Compute RUL countdown target clipped at 125
            raw_rul = total_snapshots - idx
            rul_target = min(125, raw_rul)

            row = {
                "bearing_id": bearing_id,
                "snapshot_id": idx,
                "RUL": rul_target,
                **feats
            }
            train_rows.append(row)

    if train_rows:
        train_df = pd.DataFrame(train_rows)
        merged_dfs["learning_set"] = train_df

    # 2. Process Full Test Set (Holdout Test Bearings)
    if test_dir and test_dir.exists():
        test_rows = []
        test_bearing_dirs = [d for d in test_dir.iterdir() if d.is_dir() and "bearing" in d.name.lower()]
        if not test_bearing_dirs:
            test_bearing_dirs = [d for d in test_dir.glob("*") if d.is_dir()]

        for bdir in sorted(test_bearing_dirs):
            bearing_id = bdir.name
            acc_files = sorted(
                [f for f in bdir.glob("acc_*.csv")],
                key=lambda p: int(re.search(r"\d+", p.name).group()) if re.search(r"\d+", p.name) else 0
            )
            if not acc_files:
                continue

            total_snapshots = len(acc_files)
            for idx, fpath in enumerate(acc_files, start=1):
                feats = extract_snapshot_features(fpath)
                raw_rul = total_snapshots - idx
                rul_target = min(125, raw_rul)

                row = {
                    "bearing_id": bearing_id,
                    "snapshot_id": idx,
                    "RUL": rul_target,
                    **feats
                }
                test_rows.append(row)

        if test_rows:
            test_df = pd.DataFrame(test_rows)
            merged_dfs["full_test_set"] = test_df

    return merged_dfs
