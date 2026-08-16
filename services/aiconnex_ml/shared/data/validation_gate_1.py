"""
validation_gate_1.py — VG_1: Data Validation Gate (post-split, pre-train)
==========================================================================
This gate is the checkpoint after PREPARE/ENGINEER/SPLIT and before TRAIN.
If the data quality fails below acceptable thresholds, the pipeline loops
back to the PREPARE step with corrective parameter suggestions.

Returns: (is_valid: bool, report: dict)
"""

from __future__ import annotations
from typing import Dict, Any, Tuple
import pandas as pd


def check_vg1(
    manifest: Dict[str, Any],
    df_train: pd.DataFrame | None = None,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Run Validation Gate 1 checks using information accumulated in manifest.

    Checks:
      1. Null rate in training data <= threshold (default 5%)
      2. No stuck sensors
      3. Timestamp monotonicity (if time-series)
      4. Sufficient training rows (>= 50 by default)
      5. No contract schema errors

    Returns:
        (is_valid, report):
            is_valid  — True if all checks pass, False to loop back.
            report    — Structured details of pass/fail per check.
    """
    gates_config = manifest.get("validation_gates", {}).get("vg_1", {})
    max_null_ratio = gates_config.get("max_allowed_null_ratio", 0.05)
    max_outlier_ratio = gates_config.get("max_allowed_outlier_ratio", 0.02)
    min_train_rows = gates_config.get("min_train_rows", 50)

    data_info = manifest.get("data_info", {})
    quality_report = data_info.get("quality_report", {})

    checks: Dict[str, Dict[str, Any]] = {}
    passed = True

    # Check 1: High null columns
    high_null_cols = quality_report.get("high_null_columns", {})
    check1_pass = len(high_null_cols) == 0
    checks["no_high_null_columns"] = {
        "passed": check1_pass,
        "detail": high_null_cols if not check1_pass else "OK",
    }
    if not check1_pass:
        passed = False

    # Check 2: No stuck sensors
    stuck = quality_report.get("stuck_sensors", [])
    allow_stuck = gates_config.get("allow_stuck_sensors", False)
    check2_pass = len(stuck) == 0 or allow_stuck
    checks["no_stuck_sensors"] = {
        "passed": check2_pass,
        "detail": stuck if not check2_pass else ("OK (stuck sensors allowed)" if allow_stuck and stuck else "OK"),
    }
    if not check2_pass:
        passed = False

    # Check 3: Contract errors
    contract_errors = data_info.get("contract_errors", [])
    check3_pass = len(contract_errors) == 0
    checks["schema_contract"] = {
        "passed": check3_pass,
        "detail": contract_errors if not check3_pass else "OK",
    }
    if not check3_pass:
        passed = False

    # Check 4: Timestamp monotonicity (for time-series)
    if manifest.get("data_topology", "tabular") != "tabular":
        ts_check = quality_report.get("timestamp_monotonicity", {})
        check4_pass = ts_check.get("is_monotonic", True)
        checks["timestamp_monotonic"] = {
            "passed": check4_pass,
            "detail": ts_check if not check4_pass else "OK",
        }
        if not check4_pass:
            passed = False

    # Check 5: Sufficient training rows
    if df_train is not None:
        n_train_rows = len(df_train)
        check5_pass = n_train_rows >= min_train_rows
        checks["sufficient_train_rows"] = {
            "passed": check5_pass,
            "detail": f"{n_train_rows} rows (minimum: {min_train_rows})",
        }
        if not check5_pass:
            passed = False

    report = {
        "gate": "VG_1",
        "passed": passed,
        "checks": checks,
    }

    if passed:
        print("[VG_1] ✅ Data Validation Gate PASSED. Proceeding to TRAIN.")
    else:
        failed_checks = [k for k, v in checks.items() if not v["passed"]]
        print(f"[VG_1] ❌ Data Validation Gate FAILED. Failed checks: {failed_checks}")
        print("[VG_1] Looping back to PREPARE stage...")

    manifest.setdefault("validation_results", {})
    manifest["validation_results"]["vg_1"] = report
    return passed, report
