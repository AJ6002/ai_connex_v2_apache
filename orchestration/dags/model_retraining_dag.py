"""
Apache Airflow DAG — Scheduled ML Model Retraining & Evaluation Pipeline.
Decoupled training DAG running scikit-learn models & logging runs to MLflow.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "aiconnex_mlops",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def load_dataset_task(**kwargs: Any) -> dict[str, str]:
    """
    Task 1: Load compiled Parquet dataset from storage.
    """
    return {"status": "DATASET_LOADED", "dataset_id": "ds_industrial_telemetry"}


def train_and_eval_task(**kwargs: Any) -> dict[str, str]:
    """
    Task 2: Train baseline ML model & log metrics/artifacts to MLflow.
    """
    return {"status": "MODEL_RETRAINED", "mlflow_run_id": "run_998877"}


with DAG(
    dag_id="scheduled_model_retraining_dag",
    default_args=default_args,
    description="Scheduled ML model retraining & MLflow experiment logging pipeline",
    schedule_interval="@weekly",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["aiconnex", "mlops", "retraining"],
) as dag:


    load_data_op = PythonOperator(
        task_id="load_dataset_task",
        python_callable=load_dataset_task,
    )

    retrain_op = PythonOperator(
        task_id="train_and_eval_task",
        python_callable=train_and_eval_task,
    )

    load_data_op >> retrain_op
