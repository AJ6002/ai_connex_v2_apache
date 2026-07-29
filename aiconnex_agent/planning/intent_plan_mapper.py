"""
aiconnex_agent/planning/intent_plan_mapper.py
==============================================
Sub-module 1: Deterministic Intent -> raw plan step dict lookup table.
Zero LLM calls, zero I/O. Pure business-rule mapping.
"""

from __future__ import annotations
from typing import Any, Dict, List


class IntentPlanMapper:
    """Maps a validated CUC primary_intent string to an ordered list of raw plan steps."""

    # Each entry is a list of (target_agent, task_description) tuples, in execution order.
    _PLAN_TEMPLATES: Dict[str, List[tuple]] = {
        "compile_zip": [
            ("scout", "Discover archive structure & run UnifiedCompiler"),
            ("memory", "Persist compiled dataset session context"),
        ],
        "train_rul": [
            ("scout", "Compile/profile dataset if not already compiled"),
            ("platform", "Train RUL/regression model via ML pipeline"),
            ("memory", "Persist model run results"),
        ],
        "detect_anomalies": [
            ("scout", "Compile/profile dataset if not already compiled"),
            ("platform", "Train anomaly detection model via ML pipeline"),
            ("memory", "Persist model run results"),
        ],
        "query_status": [
            ("memory", "Retrieve last session run status/metrics"),
        ],
    }

    _FALLBACK_TEMPLATE: List[tuple] = [
        ("scout", "General discovery — inspect available data sources"),
    ]

    def get_plan(self, intent: str) -> List[Dict[str, Any]]:
        """Return ordered raw step dicts for the given primary_intent. Never returns an empty list."""
        template = self._PLAN_TEMPLATES.get(intent, self._FALLBACK_TEMPLATE)
        return [
            {"step_id": f"step_{i + 1}", "target_agent": agent, "task": task}
            for i, (agent, task) in enumerate(template)
        ]
