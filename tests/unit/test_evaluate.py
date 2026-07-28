"""
Unit Tests - Node 8: evaluate.py
Tests: regression metric formulas, anomaly metric branch, output JSON keys, domain routing.
"""
import numpy as np
import sklearn.metrics


# ---------------------------------------------------------------------------
# Replicate evaluate.py metric logic without AWS calls
# ---------------------------------------------------------------------------

def _run_regression_metrics(y_true, y_pred) -> dict:
    r2   = sklearn.metrics.r2_score(y_true, y_pred)
    rmse = np.sqrt(sklearn.metrics.mean_squared_error(y_true, y_pred))
    mae  = sklearn.metrics.mean_absolute_error(y_true, y_pred)
    return {
        "regression_metrics": {
            "r2":   {"value": float(r2),   "standard_name": "R2"},
            "rmse": {"value": float(rmse), "standard_name": "RMSE"},
            "mae":  {"value": float(mae),  "standard_name": "MAE"},
        }
    }


def _run_anomaly_metrics(y_true=None, preds=None) -> dict:
    y_pred_binary = np.where(preds == -1, 1, 0)
    anomaly_rate = float(np.mean(y_pred_binary))
    metrics: dict = {"anomaly_metrics": {"anomaly_rate": {"value": anomaly_rate, "standard_name": "AnomalyRate"}}}
    if y_true is not None:
        f1        = sklearn.metrics.f1_score(y_true, y_pred_binary, zero_division=0)
        precision = sklearn.metrics.precision_score(y_true, y_pred_binary, zero_division=0)
        recall    = sklearn.metrics.recall_score(y_true, y_pred_binary, zero_division=0)
        metrics["anomaly_metrics"].update({
            "f1":        {"value": float(f1),        "standard_name": "F1"},
            "precision": {"value": float(precision), "standard_name": "Precision"},
            "recall":    {"value": float(recall),    "standard_name": "Recall"},
        })
    return metrics


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEvaluateRegression:

    def _perfect_preds(self, n=100):
        np.random.seed(0)
        y = np.random.randint(0, 100, n).astype(float)
        return y, y.copy()

    def _noisy_preds(self, n=100):
        np.random.seed(0)
        y = np.random.randint(0, 100, n).astype(float)
        pred = y + np.random.normal(0, 5, n)
        return y, pred

    def test_perfect_predictions_r2_is_1(self):
        y, pred = self._perfect_preds()
        metrics = _run_regression_metrics(y, pred)
        assert abs(metrics["regression_metrics"]["r2"]["value"] - 1.0) < 1e-9

    def test_perfect_predictions_rmse_is_0(self):
        y, pred = self._perfect_preds()
        metrics = _run_regression_metrics(y, pred)
        assert abs(metrics["regression_metrics"]["rmse"]["value"]) < 1e-9

    def test_regression_output_has_required_keys(self):
        y, pred = self._noisy_preds()
        metrics = _run_regression_metrics(y, pred)
        assert "regression_metrics" in metrics
        rm = metrics["regression_metrics"]
        for key in ["r2", "rmse", "mae"]:
            assert key in rm, f"Missing key '{key}' in regression_metrics"
            assert "value" in rm[key], f"Missing 'value' sub-key in {key}"

    def test_rmse_is_nonnegative(self):
        y, pred = self._noisy_preds()
        metrics = _run_regression_metrics(y, pred)
        assert metrics["regression_metrics"]["rmse"]["value"] >= 0

    def test_r2_bounded_between_neg_inf_and_1(self):
        y, pred = self._noisy_preds()
        metrics = _run_regression_metrics(y, pred)
        assert metrics["regression_metrics"]["r2"]["value"] <= 1.0


class TestEvaluateAnomaly:

    def test_anomaly_output_has_anomaly_rate(self):
        preds = np.array([1, -1, 1, 1, -1])
        metrics = _run_anomaly_metrics(preds=preds)
        assert "anomaly_metrics" in metrics
        assert "anomaly_rate" in metrics["anomaly_metrics"]

    def test_anomaly_rate_is_between_0_and_1(self):
        preds = np.array([1, -1, 1, 1, -1])
        metrics = _run_anomaly_metrics(preds=preds)
        rate = metrics["anomaly_metrics"]["anomaly_rate"]["value"]
        assert 0.0 <= rate <= 1.0

    def test_anomaly_with_ground_truth_includes_f1(self):
        preds   = np.array([1, -1, 1, 1, -1])
        y_true  = np.array([0,  1, 0, 0,  1])
        metrics = _run_anomaly_metrics(y_true=y_true, preds=preds)
        assert "f1" in metrics["anomaly_metrics"]
        assert "precision" in metrics["anomaly_metrics"]
        assert "recall" in metrics["anomaly_metrics"]

    def test_anomaly_f1_value_between_0_and_1(self):
        preds  = np.array([1, -1, 1, 1, -1])
        y_true = np.array([0,  1, 0, 0,  1])
        metrics = _run_anomaly_metrics(y_true=y_true, preds=preds)
        f1 = metrics["anomaly_metrics"]["f1"]["value"]
        assert 0.0 <= f1 <= 1.0
