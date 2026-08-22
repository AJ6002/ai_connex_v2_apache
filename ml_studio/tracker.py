"""
MLflow Experiment & Artifact Tracker.
Manages local MLflow tracking backend (sqlite:///mlflow.db) and run logging.
"""

import os
from typing import Any

import mlflow


class MLflowTracker:
    """
    MLflow tracking wrapper managing experiments, metrics, parameters, and model artifacts.
    """

    def __init__(self, experiment_name: str = "aiconnex_industrial_ml", tracking_uri: str | None = None):
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")

        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

    def start_run(self, run_name: str | None = None) -> Any:
        """
        Start a new MLflow tracking run.
        """
        return mlflow.start_run(run_name=run_name)

    def log_params(self, params: dict[str, Any]) -> None:
        """
        Log hyperparameters or metadata parameters.
        """
        mlflow.log_params(params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """
        Log training or evaluation metrics.
        """
        mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, local_path: str, artifact_path: str | None = None) -> None:
        """
        Log a local file artifact (e.g. Parquet dataset, JSON schema, plot).
        """
        mlflow.log_artifact(local_path, artifact_path=artifact_path)
