"""
label_contract.py — Anomaly label contract: validates supervision mode constraints
==================================================================================
Three supervision modes require different data contracts:

  supervised     → requires fault_label_column with binary/multiclass labels
  semi_supervised → requires a defined normal_period (time window of healthy data)
  unsupervised   → requires no labels at all
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, List
import pandas as pd


def validate_anomaly_label(
    df: pd.DataFrame,
    manifest: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    """
    Validate anomaly label contract based on supervision_mode.

    Returns:
        df:       Unchanged DataFrame.
        manifest: Updated with label_contract validation result.
        errors:   List of error messages (empty if all pass).
    """
    errors: List[str] = []
    label_cfg = manifest.get("label_contract", {})
    supervision_mode = label_cfg.get("supervision_mode", "unsupervised")

    print(f"[AnomalyLabelContract] Supervision mode: '{supervision_mode}'")

    if supervision_mode == "supervised":
        # Requires fault label column
        fault_col = label_cfg.get("fault_label_column")
        if not fault_col:
            errors.append("supervision_mode='supervised' requires fault_label_column to be set.")
        elif fault_col not in df.columns:
            errors.append(f"Fault label column '{fault_col}' not found in DataFrame.")
        else:
            n_classes = df[fault_col].nunique()
            n_faults = (df[fault_col] != 0).sum()
            print(f"[AnomalyLabelContract] Fault column '{fault_col}': "
                  f"{n_classes} classes, {n_faults} fault samples.")
            if n_faults == 0:
                errors.append(f"Fault column '{fault_col}' has zero positive (fault) samples.")

    elif supervision_mode == "semi_supervised":
        # Requires a normal_period definition
        normal_period = label_cfg.get("normal_period")
        if not normal_period:
            errors.append(
                "supervision_mode='semi_supervised' requires label_contract.normal_period "
                "to define the healthy training window (start/end timestamps or filter column)."
            )
        else:
            print(f"[AnomalyLabelContract] Normal period defined: {normal_period}")

    elif supervision_mode == "unsupervised":
        # No label requirements — just log
        print("[AnomalyLabelContract] Unsupervised mode — no label validation needed.")

    else:
        errors.append(f"Unknown supervision_mode: '{supervision_mode}'. "
                      f"Valid: supervised, semi_supervised, unsupervised")

    manifest.setdefault("data_info", {})
    manifest["data_info"]["anomaly_label_errors"] = errors

    if errors:
        print(f"[AnomalyLabelContract] ⚠️  {len(errors)} contract error(s):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("[AnomalyLabelContract] ✅ Label contract validated.")

    return df, manifest, errors
