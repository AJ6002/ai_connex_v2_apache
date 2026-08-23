"""
Unit tests for ML Studio BaselineTrainer and MLflowTracker.
Executes when scikit-learn and mlflow are installed (requirements-ml.txt).
"""

import pandas as pd
import pytest

try:
    import mlflow  # noqa: F401
    import sklearn  # noqa: F401

    from ml_studio.trainer import BaselineTrainer
    HAS_ML_DEPS = True
except ImportError:
    HAS_ML_DEPS = False


@pytest.mark.skipif(not HAS_ML_DEPS, reason="Heavy ML dependencies are isolated in requirements-ml.txt")
def test_baseline_classification_trainer():
    df = pd.DataFrame({
        "feature_1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "feature_2": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        "target": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    })

    trainer = BaselineTrainer(problem_type="classification", n_estimators=10, experiment_name="test_ml_experiment")
    result = trainer.train_and_evaluate(
        df=df,
        target_column="target",
        feature_columns=["feature_1", "feature_2"],
        test_size=0.3
    )

    assert result["status"] == "TRAINED"
    assert "accuracy" in result["metrics"]
    assert "f1_score" in result["metrics"]
    assert 0.0 <= result["metrics"]["accuracy"] <= 1.0


@pytest.mark.skipif(not HAS_ML_DEPS, reason="Heavy ML dependencies are isolated in requirements-ml.txt")
def test_baseline_regression_trainer():
    df = pd.DataFrame({
        "feature_1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "target": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    })

    trainer = BaselineTrainer(problem_type="regression", n_estimators=10, experiment_name="test_ml_experiment")
    result = trainer.train_and_evaluate(
        df=df,
        target_column="target",
        feature_columns=["feature_1"],
        test_size=0.3
    )

    assert result["status"] == "TRAINED"
    assert "mse" in result["metrics"]
    assert "rmse" in result["metrics"]
    assert result["metrics"]["mse"] >= 0.0
