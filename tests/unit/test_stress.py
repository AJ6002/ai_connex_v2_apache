"""
Unit Tests - Node 10: stress.py
Tests: noise injection logic, degradation metric calculation, robustness report schema.
"""
import numpy as np
import pandas as pd
import sklearn.metrics
from sklearn.ensemble import RandomForestRegressor


# ---------------------------------------------------------------------------
# Replicate stress.py noise injection + degradation logic without AWS calls
# ---------------------------------------------------------------------------

FEATURES = ["sensor_2", "sensor_3", "sensor_4"]
TARGET   = "RUL"


def _inject_noise(df: pd.DataFrame, features: list, noise_std: float = 0.1) -> pd.DataFrame:
    df_noisy = df.copy()
    for col in features:
        if pd.api.types.is_numeric_dtype(df[col]):
            noise = np.random.normal(0, noise_std * df[col].std(), len(df))
            df_noisy[col] = df[col] + noise
    return df_noisy


def _compute_degradation(model, X_clean: np.ndarray, X_noisy: np.ndarray,
                          y_true: np.ndarray) -> dict:
    rmse_clean = float(np.sqrt(sklearn.metrics.mean_squared_error(
        y_true, model.predict(X_clean)
    )))
    rmse_noisy = float(np.sqrt(sklearn.metrics.mean_squared_error(
        y_true, model.predict(X_noisy)
    )))
    degradation = (rmse_noisy - rmse_clean) / (rmse_clean + 1e-9)
    threshold   = 0.15  # 15% degradation limit
    status      = "PASSED" if degradation <= threshold else "FAILED"
    return {
        "status":           status,
        "degradation_rate": float(degradation),
        "rmse_clean":       rmse_clean,
        "rmse_noisy":       rmse_noisy,
        "threshold":        threshold,
    }


def _make_df(n: int = 80) -> pd.DataFrame:
    np.random.seed(42)
    df = pd.DataFrame({
        "global_engine_id": [i % 3 + 1 for i in range(n)],
        "cycle": list(range(1, n + 1)),
        TARGET: list(range(n - 1, -1, -1)),
    })
    for s in FEATURES:
        df[s] = np.random.normal(50, 5, n)
    return df


def _fit_model(df: pd.DataFrame):
    X = df[FEATURES].values
    y = df[TARGET].values
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStress:

    def test_noisy_df_has_same_shape(self):
        df = _make_df()
        df_noisy = _inject_noise(df, FEATURES)
        assert df_noisy.shape == df.shape

    def test_noisy_df_differs_from_clean(self):
        df = _make_df()
        df_noisy = _inject_noise(df, FEATURES, noise_std=0.5)
        for col in FEATURES:
            assert not df[col].equals(df_noisy[col]), f"Column {col} should differ after noise injection"

    def test_target_column_not_noised(self):
        df = _make_df()
        df_noisy = _inject_noise(df, FEATURES)
        pd.testing.assert_series_equal(df[TARGET], df_noisy[TARGET], check_names=True)

    def test_report_has_required_keys(self):
        np.random.seed(42)
        df = _make_df()
        model = _fit_model(df)
        df_noisy = _inject_noise(df, FEATURES, noise_std=0.1)
        report = _compute_degradation(
            model,
            df[FEATURES].values,
            df_noisy[FEATURES].values,
            df[TARGET].values,
        )
        for key in ["status", "degradation_rate", "rmse_clean", "rmse_noisy", "threshold"]:
            assert key in report, f"Missing key '{key}' in robustness report"

    def test_degradation_rate_is_float(self):
        np.random.seed(42)
        df = _make_df()
        model = _fit_model(df)
        df_noisy = _inject_noise(df, FEATURES, noise_std=0.1)
        report = _compute_degradation(
            model,
            df[FEATURES].values,
            df_noisy[FEATURES].values,
            df[TARGET].values,
        )
        assert isinstance(report["degradation_rate"], float)

    def test_clean_rmse_lower_than_noisy_on_heavy_noise(self):
        """With high noise injection, noisy RMSE should be >= clean RMSE."""
        np.random.seed(42)
        df = _make_df(n=200)
        model = _fit_model(df)
        df_noisy = _inject_noise(df, FEATURES, noise_std=5.0)  # heavy noise
        report = _compute_degradation(
            model,
            df[FEATURES].values,
            df_noisy[FEATURES].values,
            df[TARGET].values,
        )
        assert report["rmse_noisy"] >= report["rmse_clean"] - 1e-6, (
            "Noisy RMSE should be >= clean RMSE under heavy noise"
        )

    def test_status_is_valid_value(self):
        np.random.seed(42)
        df = _make_df()
        model = _fit_model(df)
        df_noisy = _inject_noise(df, FEATURES, noise_std=0.01)
        report = _compute_degradation(
            model,
            df[FEATURES].values,
            df_noisy[FEATURES].values,
            df[TARGET].values,
        )
        assert report["status"] in ("PASSED", "FAILED")
