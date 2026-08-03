"""
Unit Tests — Node 2: validate_raw.py
Tests: missing-rate check, negative time-index guard, negative-target guard, report schema.
"""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Replicate validate_raw core quality-check logic without AWS calls
# ---------------------------------------------------------------------------

def _run_raw_checks(df: pd.DataFrame, config: dict) -> dict:
    schema  = config.get("schema", {})
    thresh  = config.get("thresholds", {})
    time_idx   = schema.get("time_index", "cycle")
    target_col = schema.get("target_column")
    max_missing = thresh.get("max_missing_rate", 0.02)

    checks = {}
    passed = True

    # Check 1: missing rate
    null_total = int(df.isnull().sum().sum())
    total_cells = df.shape[0] * df.shape[1]
    actual_missing_rate = null_total / total_cells
    status = "PASS" if actual_missing_rate <= max_missing else "FAIL"
    if status == "FAIL":
        passed = False
    checks["missing_rate"] = {
        "limit": max_missing,
        "actual": actual_missing_rate,
        "status": status,
    }

    # Check 2: negative time indices
    min_time = df[time_idx].min()
    time_status = "PASS" if min_time >= 0 else "FAIL"
    if time_status == "FAIL":
        passed = False
    checks["negative_time_indices"] = {
        "actual_min": float(min_time),
        "status": time_status,
    }

    # Check 3: negative targets
    if target_col and target_col in df.columns:
        min_target = df[target_col].min()
        tgt_status = "PASS" if min_target >= 0 else "FAIL"
        if tgt_status == "FAIL":
            passed = False
        checks["negative_targets"] = {
            "actual_min": float(min_target),
            "status": tgt_status,
        }

    return {"status": "PASSED" if passed else "FAILED", "checks": checks}


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

BASE_CONFIG = {
    "schema": {"time_index": "cycle", "target_column": "RUL", "identifier": "global_engine_id"},
    "thresholds": {"max_missing_rate": 0.02},
}


def _clean_df():
    np.random.seed(1)
    return pd.DataFrame({
        "global_engine_id": list(range(1, 6)) * 8,
        "cycle": list(range(1, 41)),
        "RUL": list(range(39, -1, -1)),
        "sensor_2": np.random.normal(50, 5, 40),
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestValidateRaw:

    def test_clean_data_passes_all_checks(self):
        df = _clean_df()
        report = _run_raw_checks(df, BASE_CONFIG)
        assert report["status"] == "PASSED"
        assert report["checks"]["missing_rate"]["status"] == "PASS"
        assert report["checks"]["negative_time_indices"]["status"] == "PASS"

    def test_high_missing_rate_fails(self):
        df = _clean_df()
        df.loc[:20, "sensor_2"] = float("nan")   # > 2% nulls
        report = _run_raw_checks(df, BASE_CONFIG)
        assert report["checks"]["missing_rate"]["status"] == "FAIL"
        assert report["status"] == "FAILED"

    def test_negative_time_index_fails(self):
        df = _clean_df()
        df.loc[0, "cycle"] = -5
        report = _run_raw_checks(df, BASE_CONFIG)
        assert report["checks"]["negative_time_indices"]["status"] == "FAIL"
        assert report["status"] == "FAILED"

    def test_negative_target_fails(self):
        df = _clean_df()
        df.loc[0, "RUL"] = -10
        report = _run_raw_checks(df, BASE_CONFIG)
        assert report["checks"]["negative_targets"]["status"] == "FAIL"
        assert report["status"] == "FAILED"

    def test_report_has_required_top_level_keys(self):
        df = _clean_df()
        report = _run_raw_checks(df, BASE_CONFIG)
        assert "status" in report
        assert "checks" in report

    def test_report_checks_has_missing_rate_key(self):
        df = _clean_df()
        report = _run_raw_checks(df, BASE_CONFIG)
        assert "missing_rate" in report["checks"]

    def test_missing_rate_actual_is_numeric(self):
        df = _clean_df()
        report = _run_raw_checks(df, BASE_CONFIG)
        assert isinstance(report["checks"]["missing_rate"]["actual"], float)
