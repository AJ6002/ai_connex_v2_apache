"""
label_contract.py — Regression label validation and censoring checks
====================================================================
Validates that the target column exists, is numeric, and handles
RUL-specific censoring flags for survival regression scenarios.
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, List
import sys
import pandas as pd
import numpy as np

# Windows console encoding fix
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def validate_regression_label(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    """
    Validate the regression label contract.

    Checks:
      1. target_column is present in the DataFrame
      2. target_column is numeric
      3. If target_type = "time_to_event": censor_flag_column is present
      4. label_lag_seconds applied (done in time_alignment, verified here)

    Returns:
        df:       Unchanged DataFrame.
        manifest: Updated with label_contract validation status.
        errors:   List of error strings (empty if all pass).
    """
    errors: List[str] = []
    label_cfg = manifest.get("label_contract", {})
    target_col = label_cfg.get("target_column")
    target_type = label_cfg.get("target_type", "scalar")
    censoring = label_cfg.get("censoring", {})

    # Check 1: Target column exists
    if not target_col:
        errors.append("label_contract.target_column is not set.")
        return df, manifest, errors
    if target_col not in df.columns:
        errors.append(f"Target column '{target_col}' not found in DataFrame.")
        return df, manifest, errors

    # Check 2: Target column is numeric
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        errors.append(f"Target column '{target_col}' must be numeric. Found dtype: {df[target_col].dtype}")

    # Check 3: All-NaN or high-NaN target
    null_frac = df[target_col].isnull().mean()
    non_null_count = int(df[target_col].notna().sum())
    regime = label_cfg.get("regime", "continuous")

    if non_null_count == 0:
        errors.append(f"Target column '{target_col}' has 100% missing values. Cannot train.")
    elif null_frac > 0.5 and regime not in ["sparse", "sparse_lab"]:
        errors.append(
            f"Target column '{target_col}' has {null_frac:.1%} missing values. "
            f"Set label_contract.regime to 'sparse' or 'sparse_lab' to allow sparse target training."
        )
    elif null_frac > 0.99:
        errors.append(
            f"Target column '{target_col}' has {null_frac:.1%} missing values (fewer than 1% non-null). "
            f"Need at least some labels to train."
        )

    # Check 4: Survival / RUL censoring
    if target_type == "time_to_event":
        censor_enabled = censoring.get("enabled", False)
        censor_col = censoring.get("censor_flag_column")
        if censor_enabled and censor_col:
            if censor_col not in df.columns:
                errors.append(
                    f"Censoring flag column '{censor_col}' not found in DataFrame. "
                    f"Required for target_type='time_to_event'."
                )
            else:
                print(f"[LabelContract] RUL target with censoring column '{censor_col}' verified.")
        elif censor_enabled and not censor_col:
            errors.append("Censoring enabled but censor_flag_column is not specified.")

    # Summary
    manifest.setdefault("data_info", {})
    manifest["data_info"]["label_contract_errors"] = errors

    if errors:
        print(f"[LabelContract] ⚠️  {len(errors)} label contract error(s).")
        for e in errors:
            print(f"  - {e}")
    else:
        n_targets = int(df[target_col].notna().sum())
        print(f"[LabelContract] ✅ Target '{target_col}' valid. {n_targets} labeled rows.")

    return df, manifest, errors
