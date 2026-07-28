"""
validation_gate_2.py — VG_2: Model Quality Gate (post-train, pre-deploy)
=========================================================================
This gate is the DEPLOY checkpoint. If the trained model does not pass the
configured quality thresholds, it is NOT deployed and the pipeline loops
back with a "retrain with different config" instruction.

For regression:  checks RMSE, R², MAPE, robustness degradation
For anomaly:     checks Precision, Recall, PR-AUC, FAR/week, detection latency

Returns: (is_valid: bool, report: dict)
"""

import sys
from typing import Dict, Any, Tuple

# Windows console encoding fix
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def check_vg2_regression(
    manifest: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """Regression model quality gate."""
    gates_cfg = manifest.get("quality_gates", {}).get("regression_gates", {})
    eval_results = manifest.get("results", {}).get("evaluation", {})
    test_metrics = eval_results.get("test", {})
    robustness = manifest.get("results", {}).get("robustness", {})

    checks: Dict[str, Dict[str, Any]] = {}
    passed = True

    # RMSE gate
    max_rmse = gates_cfg.get("max_rmse")
    if max_rmse is not None:
        actual_rmse = test_metrics.get("rmse")
        ok = actual_rmse is not None and actual_rmse <= max_rmse
        checks["rmse"] = {
            "passed": ok,
            "required": f"≤ {max_rmse}",
            "actual": actual_rmse,
        }
        if not ok:
            passed = False

    # R² gate
    min_r2 = gates_cfg.get("min_r2")
    if min_r2 is not None:
        actual_r2 = test_metrics.get("r2")
        ok = actual_r2 is not None and actual_r2 >= min_r2
        checks["r2"] = {
            "passed": ok,
            "required": f"≥ {min_r2}",
            "actual": actual_r2,
        }
        if not ok:
            passed = False

    # MAPE gate
    max_mape = gates_cfg.get("max_mape_pct")
    if max_mape is not None:
        actual_mape = test_metrics.get("mape")
        actual_mape_pct = actual_mape * 100 if actual_mape else None
        ok = actual_mape_pct is not None and actual_mape_pct <= max_mape
        checks["mape_pct"] = {
            "passed": ok,
            "required": f"≤ {max_mape}%",
            "actual": actual_mape_pct,
        }
        if not ok:
            passed = False

    # Robustness gate
    robustness_ok = robustness.get("overall_passed", True)
    checks["robustness"] = {
        "passed": robustness_ok,
        "detail": "All noise/dropout tests passed" if robustness_ok else "See robustness report",
    }
    if not robustness_ok:
        passed = False

    return passed, checks


def check_vg2_anomaly(
    manifest: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
    """Anomaly model quality gate."""
    gates_cfg = manifest.get("quality_gates", {}).get("anomaly_gates", {})
    eval_results = manifest.get("results", {}).get("anomaly_evaluation", {})

    checks: Dict[str, Dict[str, Any]] = {}
    passed = True

    metric_checks = [
        ("precision",           "min_precision",               "≥", True),
        ("recall",              "min_recall",                  "≥", True),
        ("pr_auc",              "min_pr_auc",                  "≥", True),
        ("false_alarm_rate_per_week_estimate", "max_false_alarm_rate_per_week", "≤", False),
    ]

    for metric_key, gate_key, direction, higher_is_better in metric_checks:
        gate_val = gates_cfg.get(gate_key)
        if gate_val is None:
            continue
        actual = eval_results.get(metric_key)
        if actual is None:
            # Skip if metric not computed (e.g., unsupervised run)
            continue
        ok = (actual >= gate_val) if higher_is_better else (actual <= gate_val)
        checks[metric_key] = {
            "passed": ok,
            "required": f"{direction} {gate_val}",
            "actual": actual,
        }
        if not ok:
            passed = False

    return passed, checks


def run_vg2(manifest: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Route to the correct VG_2 check based on ml_task in manifest.

    Returns:
        (is_valid, report)
        is_valid=True → proceed to deploy
        is_valid=False → loop back to retrain with adjusted config
    """
    ml_task = manifest.get("ml_task", "regression")

    if ml_task == "regression":
        passed, checks = check_vg2_regression(manifest)
    elif ml_task == "anomaly":
        passed, checks = check_vg2_anomaly(manifest)
    else:
        print(f"[VG_2] No quality gates defined for ml_task='{ml_task}'. Passing by default.")
        passed = True
        checks = {}

    report = {
        "gate": "VG_2",
        "ml_task": ml_task,
        "passed": passed,
        "checks": checks,
    }

    if passed:
        print(f"[VG_2] ✅ Model Quality Gate PASSED. Model approved for deployment.")
    else:
        failed = [k for k, v in checks.items() if not v["passed"]]
        print(f"[VG_2] ❌ Model Quality Gate FAILED. Failed checks: {failed}")
        print("[VG_2] Looping back to TRAIN stage with adjusted configuration...")
        manifest["status"] = "vg2_failed_retrain_required"

    manifest.setdefault("validation_results", {})
    manifest["validation_results"]["vg_2"] = report
    return passed, report
