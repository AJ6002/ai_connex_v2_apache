"""
aiconnex_agent/telemetry/tracker.py
=====================================
AgentTelemetry — Unified cross-cutting MLflow session manager.

Provides a process-level singleton that owns a single MLflow experiment
per workflow session (wf_<hex>). All agent nodes emit telemetry through
their dedicated Emitter which calls tracker methods — keeping MLflow
initialization and run lifecycle management in one place.

Design principles:
  - One experiment per session_id: ``aiconnex_{session_id}``
  - One parent run per node type (planner, scout, platform, memory)
  - Thread-safe: uses a module-level lock for run creation
  - Always gracefully degrades when mlflow is not installed
"""

from __future__ import annotations

import json
import logging
import os
import threading
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger(__name__)

_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
_LOCK = threading.Lock()

try:
    import mlflow

    _HAS_MLFLOW = True
except ImportError:
    mlflow = None  # type: ignore[assignment]
    _HAS_MLFLOW = False


class AgentTelemetry:
    """Singleton MLflow telemetry manager for the AIConnex agent pipeline.

    Owns:
      - MLflow experiment creation keyed by session_id.
      - Safe ``log_params``, ``log_metrics``, ``log_artifact`` wrappers that
        never raise — they degrade to log-only when mlflow is unavailable.
      - ``node_run()`` context manager for opening/closing child runs per node.
    """

    def __init__(self, tracking_uri: str = _TRACKING_URI) -> None:
        self._tracking_uri = tracking_uri
        self._initialized: bool = False
        self._experiment_name: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def setup(self, session_id: str) -> None:
        """Initialize the MLflow experiment for this session.

        Idempotent — multiple calls with the same session_id are safe.
        """
        if not _HAS_MLFLOW or mlflow is None:
            return
        with _LOCK:
            if self._initialized:
                return
            try:
                os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
                mlflow.set_tracking_uri(self._tracking_uri)
                self._experiment_name = f"aiconnex_{session_id}"
                mlflow.set_experiment(self._experiment_name)
                self._initialized = True
                logger.info(
                    f"[AgentTelemetry] Experiment '{self._experiment_name}' "
                    f"ready at {self._tracking_uri}"
                )
            except Exception as exc:
                logger.debug(f"[AgentTelemetry] setup failed: {exc}")

    @contextmanager
    def node_run(self, node_name: str, session_id: str) -> Generator[Any, None, None]:
        """Context manager that wraps a single agent node execution in an MLflow run.

        Usage::

            with telemetry.node_run("scout", session_id) as run:
                telemetry.log_params({"rows": 5000})
                telemetry.log_metrics({"missing_ratio": 0.02})

        Yields the active ``mlflow.ActiveRun`` or ``None`` if mlflow is unavailable.
        """
        self.setup(session_id)
        if not _HAS_MLFLOW or mlflow is None or not self._initialized:
            yield None
            return

        run_name = f"{node_name}_{session_id}"
        try:
            with mlflow.start_run(run_name=run_name, nested=True) as run:
                mlflow.set_tag("agent_node", node_name)
                mlflow.set_tag("session_id", session_id)
                yield run
        except Exception as exc:
            logger.debug(f"[AgentTelemetry] node_run '{node_name}' error: {exc}")
            yield None

    def log_params(self, params: Dict[str, Any]) -> None:
        """Log parameters to the active MLflow run. No-op if no run is active."""
        if not _HAS_MLFLOW or mlflow is None:
            return
        try:
            # Truncate string values to MLflow 500-char limit
            safe = {k: str(v)[:500] for k, v in params.items()}
            mlflow.log_params(safe)
        except Exception as exc:
            logger.debug(f"[AgentTelemetry] log_params failed: {exc}")

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """Log metrics to the active MLflow run. No-op if no run is active."""
        if not _HAS_MLFLOW or mlflow is None:
            return
        try:
            # Filter out non-numeric values
            safe = {k: float(v) for k, v in metrics.items() if v is not None}
            mlflow.log_metrics(safe)
        except Exception as exc:
            logger.debug(f"[AgentTelemetry] log_metrics failed: {exc}")

    def log_json_artifact(self, data: Any, artifact_name: str) -> None:
        """Serialize ``data`` as JSON and log it as an MLflow artifact."""
        if not _HAS_MLFLOW or mlflow is None:
            return
        try:
            import tempfile
            import pathlib

            with tempfile.TemporaryDirectory() as tmp:
                path = pathlib.Path(tmp) / artifact_name
                path.write_text(json.dumps(data, indent=2, default=str))
                mlflow.log_artifact(str(path))
        except Exception as exc:
            logger.debug(f"[AgentTelemetry] log_json_artifact '{artifact_name}' failed: {exc}")

    def log_tag(self, key: str, value: str) -> None:
        """Set an MLflow tag on the active run."""
        if not _HAS_MLFLOW or mlflow is None:
            return
        try:
            mlflow.set_tag(key, str(value)[:500])
        except Exception as exc:
            logger.debug(f"[AgentTelemetry] log_tag failed: {exc}")


# ---------------------------------------------------------------------------
# Process-level singleton
# ---------------------------------------------------------------------------

_TELEMETRY_INSTANCE: Optional[AgentTelemetry] = None
_INSTANCE_LOCK = threading.Lock()


def get_telemetry() -> AgentTelemetry:
    """Return the process-level AgentTelemetry singleton."""
    global _TELEMETRY_INSTANCE
    if _TELEMETRY_INSTANCE is None:
        with _INSTANCE_LOCK:
            if _TELEMETRY_INSTANCE is None:
                _TELEMETRY_INSTANCE = AgentTelemetry()
    return _TELEMETRY_INSTANCE


def reset_telemetry() -> None:
    """Reset the singleton. For testing purposes only."""
    global _TELEMETRY_INSTANCE
    with _INSTANCE_LOCK:
        _TELEMETRY_INSTANCE = None
