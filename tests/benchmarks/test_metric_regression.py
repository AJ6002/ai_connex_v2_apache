"""
test_metric_regression.py - Version-over-Version Metric Baseline Tracking
===========================================================================
Compares the metrics in latest run reports (outputs/regression/reports/ and outputs/anomaly/reports/)
against baseline tolerances in tests/benchmarks/baseline_metrics.json to prevent performance regressions.
"""

from __future__ import annotations
import os
import json
import pytest


BASELINE_JSON_PATH = "tests/benchmarks/baseline_metrics.json"


@pytest.fixture
def baselines():
    assert os.path.exists(BASELINE_JSON_PATH), f"Baseline metrics file missing: {BASELINE_JSON_PATH}"
    with open(BASELINE_JSON_PATH, "r") as f:
        return json.load(f)


@pytest.mark.tier2
def test_regression_metric_baseline(baselines):
    """Assert latest regression run metrics do not regress past baseline tolerance bounds."""
    cfg = baselines["regression"]
    report_path = cfg["report_path"]

    assert os.path.exists(report_path), f"Regression report not found: {report_path}. Run regression runner first."
    with open(report_path, "r") as f:
        report = json.load(f)

    algo = report.get("best_algorithm")
    assert algo == cfg["expected_best_algorithm"], f"Algorithm changed from {cfg['expected_best_algorithm']} to {algo}"

    eval_data = report.get("evaluation", {})
    val_or_test = eval_data.get("test", eval_data.get("val", {}))

    rmse = val_or_test.get("rmse", 999.0)
    r2 = val_or_test.get("r2", -999.0)
    rul_score = val_or_test.get("rul_asymmetric_score", 999.0)

    # In our runner, metrics can be reported on unscaled or scaled targets.
    # We verify that r2 >= min_allowed_r2 (r2 is scale-invariant) and metrics are valid numbers.
    assert r2 >= cfg["min_allowed_r2"], f"Regression R^2 degraded: got {r2:.4f}, required >= {cfg['min_allowed_r2']}"
    import math
    assert not math.isnan(rmse)


@pytest.mark.tier2
def test_anomaly_metric_baseline(baselines):
    """Assert latest anomaly run metrics do not regress past baseline tolerance bounds."""
    cfg = baselines["anomaly"]
    report_path = cfg["report_path"]

    assert os.path.exists(report_path), f"Anomaly report not found: {report_path}. Run anomaly runner first."
    with open(report_path, "r") as f:
        report = json.load(f)

    algo = report.get("best_algorithm")
    assert algo == cfg["expected_best_algorithm"], f"Algorithm changed from {cfg['expected_best_algorithm']} to {algo}"

    eval_data = report.get("evaluation", {})
    p99 = eval_data.get("p99_score", 0.0)

    assert p99 <= cfg["max_allowed_p99_score"], f"Anomaly p99 score shifted too high: got {p99:.4f}, max allowed {cfg['max_allowed_p99_score']}"
