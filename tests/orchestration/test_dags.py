"""
Unit tests for Apache Airflow DAG structures and task callables.
Executes when apache-airflow is present in the runtime environment.
"""

import importlib.util
from pathlib import Path

import pytest

try:
    import airflow  # noqa: F401
    HAS_AIRFLOW = True
except ImportError:
    HAS_AIRFLOW = False

_dags_dir = Path(__file__).resolve().parent.parent.parent / "orchestration" / "dags"

if HAS_AIRFLOW:
    _ingest_path = _dags_dir / "batch_ingestion_dag.py"
    _ingest_spec = importlib.util.spec_from_file_location("batch_ingestion_mod", _ingest_path)
    assert _ingest_spec is not None and _ingest_spec.loader is not None
    _ingest_mod = importlib.util.module_from_spec(_ingest_spec)
    _ingest_spec.loader.exec_module(_ingest_mod)

    _retrain_path = _dags_dir / "model_retraining_dag.py"
    _retrain_spec = importlib.util.spec_from_file_location("model_retraining_mod", _retrain_path)
    assert _retrain_spec is not None and _retrain_spec.loader is not None
    _retrain_mod = importlib.util.module_from_spec(_retrain_spec)
    _retrain_spec.loader.exec_module(_retrain_mod)


@pytest.mark.skipif(not HAS_AIRFLOW, reason="Apache Airflow is isolated in docker-compose.airflow.yml")
def test_batch_ingestion_dag_structure():
    dag = _ingest_mod.dag
    assert dag is not None
    assert dag.dag_id == "batch_dataset_ingestion_dag"
    assert len(dag.tasks) == 2
    task_ids = [t.task_id for t in dag.tasks]
    assert "batch_intake_task" in task_ids
    assert "parquet_compile_task" in task_ids


@pytest.mark.skipif(not HAS_AIRFLOW, reason="Apache Airflow is isolated in docker-compose.airflow.yml")
def test_batch_intake_callables():
    res1 = _ingest_mod.batch_intake_task()
    assert res1["status"] == "BATCH_INTAKE_SUCCESS"

    res2 = _ingest_mod.parquet_compile_task()
    assert res2["status"] == "PARQUET_COMPILED"


@pytest.mark.skipif(not HAS_AIRFLOW, reason="Apache Airflow is isolated in docker-compose.airflow.yml")
def test_model_retraining_dag_structure():
    dag = _retrain_mod.dag
    assert dag is not None
    assert dag.dag_id == "scheduled_model_retraining_dag"
    assert len(dag.tasks) == 2
    task_ids = [t.task_id for t in dag.tasks]
    assert "load_dataset_task" in task_ids
    assert "train_and_eval_task" in task_ids


@pytest.mark.skipif(not HAS_AIRFLOW, reason="Apache Airflow is isolated in docker-compose.airflow.yml")
def test_model_retraining_callables():
    res1 = _retrain_mod.load_dataset_task()
    assert res1["status"] == "DATASET_LOADED"

    res2 = _retrain_mod.train_and_eval_task()
    assert res2["status"] == "MODEL_RETRAINED"
