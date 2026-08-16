"""
scaling.py — Train-only scaler fit with transform on all splits
================================================================
CRITICAL RULE: Scaler MUST be fit on training data only.
Fitting on val or test data causes target leakage.
"""

from __future__ import annotations
import os
import pickle
from typing import Dict, Any, List, Tuple
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler


SCALER_MAP = {
    "standard": StandardScaler,
    "robust": RobustScaler,
    "minmax": MinMaxScaler,
}


def fit_scaler(
    df_train: pd.DataFrame,
    feature_cols: List[str],
    method: str = "standard",
) -> Any:
    """
    Fit a scaler on the training split only.

    Args:
        df_train:     Training DataFrame.
        feature_cols: Columns to scale.
        method:       'standard', 'robust', or 'minmax'.

    Returns:
        Fitted scaler object.
    """
    if method not in SCALER_MAP:
        raise ValueError(f"Unknown scaler method: '{method}'. Choose: {list(SCALER_MAP.keys())}")
    scaler_cls = SCALER_MAP[method]
    scaler = scaler_cls()
    scaler.fit(df_train[feature_cols])
    print(f"[Scaling] Fitted {scaler_cls.__name__} on {len(feature_cols)} features (train only).")
    return scaler


def apply_scaler(
    df: pd.DataFrame,
    scaler: Any,
    feature_cols: List[str],
) -> pd.DataFrame:
    """
    Transform a DataFrame using a pre-fitted scaler.
    Only scales `feature_cols` — other columns (target, entity, timestamp) are unchanged.
    """
    df = df.copy()
    df[feature_cols] = scaler.transform(df[feature_cols])
    return df


def fit_and_apply_all_splits(
    df_train: pd.DataFrame,
    df_val: pd.DataFrame,
    df_test: pd.DataFrame,
    feature_cols: List[str],
    method: str = "standard",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Any]:
    """
    Full pipeline: fit on train, apply to train/val/test.

    Returns:
        df_train_scaled, df_val_scaled, df_test_scaled, fitted_scaler
    """
    scaler = fit_scaler(df_train, feature_cols, method)
    df_train = apply_scaler(df_train, scaler, feature_cols)
    df_val = apply_scaler(df_val, scaler, feature_cols)
    df_test = apply_scaler(df_test, scaler, feature_cols)
    return df_train, df_val, df_test, scaler


def save_scaler(scaler: Any, path: str) -> str:
    """Pickle and save the fitted scaler to disk."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"[Scaling] Scaler saved: {path}")
    return path


def load_scaler(path: str) -> Any:
    """Load a pickled scaler from disk."""
    with open(path, "rb") as f:
        return pickle.load(f)
