"""
Baseline ML Model Trainer Engine.
Trains Scikit-Learn classification & regression models and logs runs to MLflow.
"""

from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error
from sklearn.model_selection import train_test_split

from ml_studio.tracker import MLflowTracker


class BaselineTrainer:
    """
    Scikit-Learn baseline model trainer with integrated MLflow experiment logging.
    """

    def __init__(
        self,
        problem_type: Literal["classification", "regression"] = "classification",
        n_estimators: int = 100,
        random_state: int = 42,
        experiment_name: str = "aiconnex_industrial_ml"
    ):
        self.problem_type = problem_type
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.tracker = MLflowTracker(experiment_name=experiment_name)

    def train_and_evaluate(
        self,
        df: pd.DataFrame,
        target_column: str,
        feature_columns: list[str],
        test_size: float = 0.2
    ) -> dict[str, Any]:
        """
        Train baseline model on feature columns, evaluate performance, and log to MLflow.
        """
        X = df[feature_columns]
        y = df[target_column]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state
        )

        if self.problem_type == "classification":
            model = RandomForestClassifier(n_estimators=self.n_estimators, random_state=self.random_state)
        else:
            model = RandomForestRegressor(n_estimators=self.n_estimators, random_state=self.random_state)

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        metrics: dict[str, float] = {}
        if self.problem_type == "classification":
            metrics["accuracy"] = float(accuracy_score(y_test, predictions))
            metrics["f1_score"] = float(f1_score(y_test, predictions, average="weighted"))
        else:
            metrics["mse"] = float(mean_squared_error(y_test, predictions))
            metrics["rmse"] = float(np.sqrt(metrics["mse"]))

        params = {
            "problem_type": self.problem_type,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "target_column": target_column,
            "num_features": len(feature_columns),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        with self.tracker.start_run(run_name=f"baseline_{self.problem_type}"):
            self.tracker.log_params(params)
            self.tracker.log_metrics(metrics)

        return {
            "status": "TRAINED",
            "model": model,
            "metrics": metrics,
            "params": params
        }
