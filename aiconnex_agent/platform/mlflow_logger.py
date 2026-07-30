# aiconnex_agent/platform/mlflow_logger.py
"""
MLflow Logger (Phase 5c)
==========================
Logs multi-candidate experiment results, leaderboard, meta-learner weights, and winner selection
to MLflow local file store (./mlruns). Zero external server dependencies.

If mlflow is not installed, all calls gracefully degrade to no-ops and
return a fallback dict — the agent pipeline never fails due to missing
tracking infrastructure.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np

from aiconnex_agent.schemas import ScorerReport, JudgeReport, SelectionResult

logger = logging.getLogger(__name__)

try:
    import mlflow
    _HAS_MLFLOW = True
except ImportError:
    mlflow = None  # type: ignore[assignment]
    _HAS_MLFLOW = False

_TRACKING_URI = "./mlruns"


def log_experiment(
    session_id: str,
    selection_result: SelectionResult,
    scorer_reports: List[ScorerReport],
    judge_reports: List[JudgeReport],
    ensemble_weights: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Log the full multi-candidate experiment to MLflow.

    Args:
        session_id: Workflow session ID (wf_<hex>).
        selection_result: The Selector Agent's output with leaderboard.
        scorer_reports: All candidate Scorer reports.
        judge_reports: All candidate Judge reports.
        ensemble_weights: Non-negative Ridge meta-learner coefficients (Remediation 6).

    Returns:
        Dict with ``run_id``, ``experiment_name``, ``tracking_uri``,
        and ``status`` keys.
    """
    if not _HAS_MLFLOW or mlflow is None:
        logger.warning("[MLflowLogger] mlflow not installed — skipping experiment logging.")
        return {"status": "mlflow_unavailable", "session_id": session_id}

    experiment_name = f"aiconnex_{session_id}"
    mlflow.set_tracking_uri(_TRACKING_URI)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=f"ensemble_run_{session_id}") as run:
        # Log winner parameters
        mlflow.log_param("session_id", session_id)
        mlflow.log_param("winner_model_id", selection_result.winner_model_id)
        mlflow.log_param("winner_dag_id", selection_result.winner_dag_id)
        mlflow.log_param("is_ensemble", selection_result.is_ensemble)
        mlflow.log_param("num_candidates", len(scorer_reports))

        # Log ensemble meta-learner weights if available (Remediation 6)
        if ensemble_weights is not None:
            for k, w in enumerate(ensemble_weights):
                mlflow.log_param(f"meta_weight_base_{k}", float(w))

        # Log winner metrics
        winner_scorer = next(
            (sr for sr in scorer_reports if sr.recipe_id == selection_result.winner_model_id),
            None,
        )
        if winner_scorer:
            mlflow.log_metrics({
                "winner_r2": winner_scorer.r2_score,
                "winner_rmse": winner_scorer.rmse,
                "winner_mae": winner_scorer.mae,
                "winner_mape": winner_scorer.mape,
                "winner_latency_ms": winner_scorer.latency_ms,
                "winner_model_size_mb": winner_scorer.model_size_mb,
            })

        # Log all candidate metrics with prefix
        for i, sr in enumerate(scorer_reports):
            mlflow.log_metrics({
                f"candidate_{i}_r2": sr.r2_score,
                f"candidate_{i}_rmse": sr.rmse,
                f"candidate_{i}_mae": sr.mae,
            })

        # Log leaderboard as a table tag
        lb_summary = " | ".join(
            f"#{e.rank} {e.model_id} (R²={e.r2_score:.4f})"
            for e in selection_result.leaderboard
        )
        mlflow.set_tag("leaderboard_summary", lb_summary[:250])
        mlflow.set_tag("selection_rationale", selection_result.selection_rationale[:250])

        run_id = run.info.run_id

    logger.info(f"[MLflowLogger] Experiment '{experiment_name}' logged. Run ID: {run_id}")
    return {
        "status": "logged",
        "run_id": run_id,
        "experiment_name": experiment_name,
        "tracking_uri": _TRACKING_URI,
        "session_id": session_id,
    }
