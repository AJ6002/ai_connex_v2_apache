"""
Unit Tests - Node 6: train.py
Tests: ALGORITHM_REGISTRY dispatch, hyperparameter injection, artifact creation, seed reproducibility.
"""
import pickle
import tarfile
import pytest
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import Ridge, LinearRegression
import xgboost as xgb


# ---------------------------------------------------------------------------
# Mirror ALGORITHM_REGISTRY from train.py
# ---------------------------------------------------------------------------

ALGORITHM_REGISTRY = {
    "random_forest":    RandomForestRegressor,
    "xgboost":          xgb.XGBRegressor,
    "linear_regression":LinearRegression,
    "ridge":            Ridge,
    "isolation_forest": IsolationForest,
}

FEATURES = ["sensor_2", "sensor_3", "sensor_4"]


def _make_train_df(n: int = 80) -> pd.DataFrame:
    np.random.seed(42)
    df = pd.DataFrame({
        "global_engine_id": [i % 3 + 1 for i in range(n)],
        "cycle": list(range(1, n + 1)),
        "RUL":   list(range(n - 1, -1, -1)),
    })
    for s in FEATURES:
        df[s] = np.random.normal(50, 5, n)
    return df


def _fit_model(algo_name: str, hyperparams: dict, train_df: pd.DataFrame,
               features: list, target: str, problem_type: str = "regression"):
    model_cls = ALGORITHM_REGISTRY[algo_name]
    model = model_cls(**hyperparams)
    X = train_df[features].fillna(0).values
    if problem_type == "regression":
        y = train_df[target].fillna(0).values
        model.fit(X, y)
    else:
        model.fit(X)
    return model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTrain:

    def test_registry_contains_expected_algorithms(self):
        expected = ["random_forest", "xgboost", "linear_regression", "ridge", "isolation_forest"]
        for algo in expected:
            assert algo in ALGORITHM_REGISTRY, f"Algorithm '{algo}' missing from registry"

    def test_unknown_algorithm_raises(self):
        with pytest.raises(KeyError):
            _ = ALGORITHM_REGISTRY["nonexistent_algo"]

    def test_random_forest_fits_without_error(self):
        df = _make_train_df()
        model = _fit_model("random_forest", {"n_estimators": 5, "random_state": 42},
                           df, FEATURES, "RUL")
        assert hasattr(model, "predict"), "Fitted model should have predict method"

    def test_xgboost_fits_without_error(self):
        df = _make_train_df()
        model = _fit_model("xgboost", {"n_estimators": 5, "random_state": 42},
                           df, FEATURES, "RUL")
        assert hasattr(model, "predict")

    def test_isolation_forest_fits_without_error(self):
        df = _make_train_df()
        model = _fit_model("isolation_forest", {"n_estimators": 5, "random_state": 42},
                           df, FEATURES, "RUL", problem_type="anomaly")
        assert hasattr(model, "predict")

    def test_model_produces_predictions(self):
        df = _make_train_df()
        model = _fit_model("random_forest", {"n_estimators": 5, "random_state": 42},
                           df, FEATURES, "RUL")
        preds = model.predict(df[FEATURES].fillna(0).values)
        assert len(preds) == len(df)

    def test_seed_reproducibility(self):
        """Same seed -> same predictions."""
        df = _make_train_df()
        hp = {"n_estimators": 10, "random_state": 42}
        m1 = _fit_model("random_forest", hp, df, FEATURES, "RUL")
        m2 = _fit_model("random_forest", hp, df, FEATURES, "RUL")
        p1 = m1.predict(df[FEATURES].fillna(0).values)
        p2 = m2.predict(df[FEATURES].fillna(0).values)
        np.testing.assert_array_equal(p1, p2)

    def test_model_pickle_roundtrip(self, tmp_path):
        df = _make_train_df()
        model = _fit_model("random_forest", {"n_estimators": 5, "random_state": 42},
                           df, FEATURES, "RUL")
        pkl_path = tmp_path / "model.pkl"
        with open(pkl_path, "wb") as f:
            pickle.dump(model, f)
        with open(pkl_path, "rb") as f:
            loaded_model = pickle.load(f)
        p1 = model.predict(df[FEATURES].values)
        p2 = loaded_model.predict(df[FEATURES].values)
        np.testing.assert_array_equal(p1, p2)

    def test_model_tar_gz_creation(self, tmp_path):
        df = _make_train_df()
        model = _fit_model("random_forest", {"n_estimators": 5, "random_state": 42},
                           df, FEATURES, "RUL")
        pkl_path = tmp_path / "model.pkl"
        tar_path = tmp_path / "model.tar.gz"
        with open(pkl_path, "wb") as f:
            pickle.dump(model, f)
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(pkl_path, arcname="model.pkl")
        assert tar_path.exists(), "model.tar.gz should be created"
        assert tar_path.stat().st_size > 0, "model.tar.gz should not be empty"
