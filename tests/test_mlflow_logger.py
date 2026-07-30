# tests/test_mlflow_logger.py
"""Tests for MLflow Logger (Phase 5c). Uses mock MLflow to avoid real tracking dependency."""

from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock

from aiconnex_agent.schemas import (
    ScorerReport, JudgeReport, SelectionResult, LeaderboardEntry,
)
from aiconnex_agent.platform.mlflow_logger import log_experiment


def _make_test_data():
    scorers = [
        ScorerReport(recipe_id="A", r2_score=0.90, rmse=15.0, mae=10.0, mape=5.0, latency_ms=10, model_size_mb=1.0),
        ScorerReport(recipe_id="B", r2_score=0.95, rmse=10.0, mae=7.0, mape=3.0, latency_ms=8, model_size_mb=0.5),
    ]
    judges = [
        JudgeReport(recipe_id="A", qualitative_score=0.7, rubric_ratings={}, reasoning="ok", risk_assessment="medium"),
        JudgeReport(recipe_id="B", qualitative_score=0.9, rubric_ratings={}, reasoning="good", risk_assessment="low"),
    ]
    leaderboard = [
        LeaderboardEntry(rank=1, model_id="B", dag_id="DAG_414", algo_name="LightGBM",
                         composite_score=0.93, r2_score=0.95, rmse=10.0, mae=7.0, is_winner=True),
        LeaderboardEntry(rank=2, model_id="A", dag_id="DAG_241", algo_name="RandomForest",
                         composite_score=0.85, r2_score=0.90, rmse=15.0, mae=10.0, is_winner=False),
    ]
    selection = SelectionResult(
        winner_model_id="B", winner_dag_id="DAG_414", is_ensemble=False,
        selection_rationale="Best composite score.", leaderboard=leaderboard,
    )
    return scorers, judges, selection


@patch("aiconnex_agent.platform.mlflow_logger.mlflow")
def test_log_experiment_returns_run_info(mock_mlflow):
    """log_experiment should return a dict with run_id and experiment_name."""
    mock_run = MagicMock()
    mock_run.info.run_id = "abc123"
    mock_mlflow.start_run.return_value.__enter__ = MagicMock(return_value=mock_run)
    mock_mlflow.start_run.return_value.__exit__ = MagicMock(return_value=False)

    scorers, judges, selection = _make_test_data()
    result = log_experiment("wf_test1234", selection, scorers, judges)

    assert "run_id" in result
    assert "experiment_name" in result
    mock_mlflow.set_experiment.assert_called_once()


@patch("aiconnex_agent.platform.mlflow_logger.mlflow")
def test_log_experiment_logs_winner_metrics(mock_mlflow):
    """Should log the winner's metrics via mlflow.log_metrics."""
    mock_run = MagicMock()
    mock_run.info.run_id = "xyz789"
    mock_mlflow.start_run.return_value.__enter__ = MagicMock(return_value=mock_run)
    mock_mlflow.start_run.return_value.__exit__ = MagicMock(return_value=False)

    scorers, judges, selection = _make_test_data()
    log_experiment("wf_test5678", selection, scorers, judges)

    mock_mlflow.log_metrics.assert_called()


def test_log_experiment_graceful_without_mlflow():
    """If mlflow is not installed, log_experiment should return a fallback dict."""
    with patch.dict("sys.modules", {"mlflow": None}):
        import importlib
        import aiconnex_agent.platform.mlflow_logger as mod
        importlib.reload(mod)

        scorers, judges, selection = _make_test_data()
        result = mod.log_experiment("wf_nomlflow", selection, scorers, judges)
        assert result.get("status") in ("mlflow_unavailable", "logged")
