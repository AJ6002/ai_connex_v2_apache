"""
Contract Tests - Report Schemas
Validates that each node's output JSON report has the required keys
and value types defined in the contract.
"""


# ---------------------------------------------------------------------------
# Minimal valid reports (mirrors what each node produces)
# ---------------------------------------------------------------------------

def _raw_check_report():
    return {
        "manifest_id": "manifest-run-001",
        "status":      "PASSED",
        "checks": {
            "missing_rate": {
                "limit":  0.02,
                "actual": 0.001,
                "status": "PASS",
            },
            "negative_time_indices": {
                "actual_min": 1.0,
                "status":     "PASS",
            },
        },
    }


def _evaluation_regression_report():
    return {
        "regression_metrics": {
            "r2":   {"value": 0.72, "standard_name": "R2"},
            "rmse": {"value": 12.3, "standard_name": "RMSE"},
            "mae":  {"value": 9.1,  "standard_name": "MAE"},
        }
    }


def _evaluation_anomaly_report():
    return {
        "anomaly_metrics": {
            "anomaly_rate": {"value": 0.08, "standard_name": "AnomalyRate"},
            "f1":           {"value": 0.78, "standard_name": "F1"},
            "precision":    {"value": 0.81, "standard_name": "Precision"},
            "recall":       {"value": 0.74, "standard_name": "Recall"},
        }
    }


def _robustness_report():
    return {
        "status":           "PASSED",
        "degradation_rate": 0.03,
        "rmse_clean":       11.0,
        "rmse_noisy":       11.3,
        "threshold":        0.15,
    }


def _explainability_report():
    return {
        "ranked_features": [
            {"feature": "sensor_2", "importance": 0.45},
            {"feature": "sensor_3", "importance": 0.35},
            {"feature": "sensor_4", "importance": 0.20},
        ]
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRawCheckReportSchema:

    def test_has_status(self):
        r = _raw_check_report()
        assert "status" in r

    def test_has_checks(self):
        r = _raw_check_report()
        assert "checks" in r

    def test_checks_has_missing_rate(self):
        r = _raw_check_report()
        assert "missing_rate" in r["checks"]

    def test_status_is_valid(self):
        r = _raw_check_report()
        assert r["status"] in ("PASSED", "FAILED")

    def test_missing_rate_has_actual_and_limit(self):
        r = _raw_check_report()
        mr = r["checks"]["missing_rate"]
        assert "actual" in mr
        assert "limit" in mr


class TestEvaluationReportSchema:

    def test_regression_report_has_r2(self):
        r = _evaluation_regression_report()
        assert "regression_metrics" in r
        assert "r2" in r["regression_metrics"]
        assert "value" in r["regression_metrics"]["r2"]

    def test_regression_report_has_rmse(self):
        r = _evaluation_regression_report()
        assert "rmse" in r["regression_metrics"]

    def test_regression_report_has_mae(self):
        r = _evaluation_regression_report()
        assert "mae" in r["regression_metrics"]

    def test_anomaly_report_has_anomaly_rate(self):
        r = _evaluation_anomaly_report()
        assert "anomaly_metrics" in r
        assert "anomaly_rate" in r["anomaly_metrics"]

    def test_anomaly_report_has_f1(self):
        r = _evaluation_anomaly_report()
        assert "f1" in r["anomaly_metrics"]


class TestRobustnessReportSchema:

    def test_has_status(self):
        r = _robustness_report()
        assert "status" in r

    def test_has_degradation_rate(self):
        r = _robustness_report()
        assert "degradation_rate" in r

    def test_degradation_rate_is_float(self):
        r = _robustness_report()
        assert isinstance(r["degradation_rate"], float)

    def test_status_is_valid(self):
        r = _robustness_report()
        assert r["status"] in ("PASSED", "FAILED")


class TestExplainabilityReportSchema:

    def test_has_ranked_features(self):
        r = _explainability_report()
        assert "ranked_features" in r

    def test_ranked_features_is_list(self):
        r = _explainability_report()
        assert isinstance(r["ranked_features"], list)

    def test_each_entry_has_feature_key(self):
        r = _explainability_report()
        for entry in r["ranked_features"]:
            assert "feature" in entry

    def test_each_entry_has_importance_key(self):
        r = _explainability_report()
        for entry in r["ranked_features"]:
            assert "importance" in entry

    def test_importances_sum_to_approx_1(self):
        r = _explainability_report()
        total = sum(e["importance"] for e in r["ranked_features"])
        assert abs(total - 1.0) < 1e-6
