"""
mode_normalization.py — Per-operating-mode feature normalization
================================================================
Industrial equipment operates in multiple distinct modes (startup, steady-state,
shutdown, CIP/cleaning). Normalizing features globally across all modes causes
the model to interpret regime transitions as anomalies (alarm fatigue).

This module fits a separate scaler per operating mode and applies mode-aware
normalization during both training and inference.

Requires: manifest["operating_modes"]["enabled"] = true
          manifest["operating_modes"]["mode_column"] = "operating_regime"
"""

from __future__ import annotations
import os
import pickle
from typing import Dict, Any, List, Tuple
import pandas as pd
from sklearn.preprocessing import StandardScaler


def fit_per_mode_scalers(
    df_train: pd.DataFrame,
    feature_cols: List[str],
    mode_col: str,
) -> Dict[str, Any]:
    """
    Fit one StandardScaler per unique operating mode in the training data.

    Returns:
        {mode_label: fitted_scaler}
    """
    mode_scalers: Dict[str, Any] = {}
    for mode, grp in df_train.groupby(mode_col):
        scaler = StandardScaler()
        scaler.fit(grp[feature_cols])
        mode_scalers[str(mode)] = scaler
        print(f"[ModeNorm] Fitted scaler for mode '{mode}' ({len(grp)} rows).")
    return mode_scalers


def apply_per_mode_scaling(
    df: pd.DataFrame,
    feature_cols: List[str],
    mode_col: str,
    mode_scalers: Dict[str, Any],
    fallback_scaler: Any | None = None,
) -> pd.DataFrame:
    """
    Apply per-mode scaling to a DataFrame.
    Rows belonging to an unseen mode use the fallback_scaler (if provided),
    otherwise they are left unscaled with a warning.
    """
    df = df.copy()
    for mode, grp_idx in df.groupby(mode_col).groups.items():
        mode_key = str(mode)
        if mode_key in mode_scalers:
            df.loc[grp_idx, feature_cols] = mode_scalers[mode_key].transform(
                df.loc[grp_idx, feature_cols]
            )
        elif fallback_scaler is not None:
            print(f"[ModeNorm] ⚠️  Unknown mode '{mode}'. Using global fallback scaler.")
            df.loc[grp_idx, feature_cols] = fallback_scaler.transform(
                df.loc[grp_idx, feature_cols]
            )
        else:
            print(f"[ModeNorm] ⚠️  Unknown mode '{mode}'. No fallback — leaving unscaled.")
    return df


def save_mode_scalers(mode_scalers: Dict[str, Any], path: str) -> str:
    """Pickle and save the dict of per-mode scalers."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(mode_scalers, f)
    print(f"[ModeNorm] Mode scalers saved: {path}")
    return path


def load_mode_scalers(path: str) -> Dict[str, Any]:
    """Load pickled per-mode scalers."""
    with open(path, "rb") as f:
        return pickle.load(f)
