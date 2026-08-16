"""
contract.py — Schema enforcement: dtype checks, required columns, value ranges
==============================================================================
Validates the DataFrame conforms to the expected schema defined in the manifest
before any feature engineering or modeling starts.
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import pandas as pd


def check_required_columns(
    df: pd.DataFrame,
    required: List[str],
) -> List[str]:
    """Return list of required columns that are missing from df."""
    return [col for col in required if col not in df.columns]


def check_dtype_compatibility(
    df: pd.DataFrame,
    expected_numeric: List[str],
) -> Dict[str, str]:
    """
    Return columns declared as numeric but found to be non-numeric.
    {col: actual_dtype}
    """
    mismatches = {}
    for col in expected_numeric:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            mismatches[col] = str(df[col].dtype)
    return mismatches


def enforce_contract(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    """
    Enforce schema contract defined in manifest['schema_config'].

    Returns:
        df:       Unchanged DataFrame (validation only, no mutation).
        manifest: Updated with contract_errors list.
        errors:   List of human-readable error strings.
    """
    errors: List[str] = []
    schema = manifest.get("schema_config", {})

    # Check required feature columns
    raw_features = schema.get("raw_features", [])
    if raw_features:
        missing = check_required_columns(df, raw_features)
        if missing:
            errors.append(f"Missing required feature columns: {missing}")

    # Check target column for regression
    label_contract = manifest.get("label_contract", {})
    target_col = label_contract.get("target_column")
    if target_col and target_col not in df.columns:
        errors.append(f"Target column '{target_col}' not found in DataFrame.")

    # Check entity column if multi-entity
    entity_col = schema.get("entity_column")
    if entity_col and entity_col not in df.columns:
        errors.append(f"Entity column '{entity_col}' not found in DataFrame.")

    # Check timestamp column
    ts_col = schema.get("timestamp_column")
    if ts_col and ts_col not in df.columns:
        errors.append(f"Timestamp column '{ts_col}' not found in DataFrame.")

    # Check dtype mismatches for declared features
    if raw_features:
        dtype_issues = check_dtype_compatibility(df, raw_features)
        for col, actual in dtype_issues.items():
            errors.append(f"Column '{col}' expected numeric but found dtype '{actual}'.")

    if errors:
        print(f"[Contract] ⚠️  {len(errors)} schema violations found.")
        for e in errors:
            print(f"  - {e}")
    else:
        print("[Contract] ✅ Schema contract validated.")

    manifest.setdefault("data_info", {})
    manifest["data_info"]["contract_errors"] = errors
    return df, manifest, errors


def validate_or_raise(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run contract validation and raise ValueError on any schema error.
    Use this in strict mode (e.g., during production inference).
    """
    df, manifest, errors = enforce_contract(df, manifest)
    if errors:
        raise ValueError(
            f"Schema contract failed with {len(errors)} error(s):\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
    return df, manifest
