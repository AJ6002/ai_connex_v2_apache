"""
aiconnex_agent/planning/intent_plan_mapper.py
==============================================
Sub-module 1: Deterministic Intent -> raw plan step dict lookup table.
Zero LLM calls, zero I/O. Pure business-rule mapping.

Architecture note: Platform Agent steps are NOT included in the initial
plan template. They are enqueued dynamically AFTER the user selects a
recipe from the AnalyticalRecipe catalog during the HITL step.
The Planner's responsibility ends at: Compile → Catalog → User Selects.
"""

from __future__ import annotations
from typing import Any, Dict, List


class IntentPlanMapper:
    """Maps a validated CUC primary_intent string to an ordered list of raw plan steps."""

    # Each entry is a list of (target_agent, task_description) tuples, in execution order.
    _PLAN_TEMPLATES: Dict[str, List[tuple]] = {
        # User wants to compile + get a recipe catalog — no modelling yet
        "compile_zip": [
            ("scout", "Discover archive structure, run UnifiedCompiler & build Recipe Catalog"),
            ("memory", "Persist compiled dataset and recipe catalog to session context"),
        ],
        # User mentions training — we still compile + catalog first, then platform executes
        # the recipe chosen by the user during HITL (not hardcoded here)
        "train_rul": [
            ("scout", "Compile/profile dataset & generate Analytical Recipe Catalog"),
            ("memory", "Persist recipe catalog to session context"),
            # Platform steps are appended dynamically after HITL recipe selection
        ],
        "detect_anomalies": [
            ("scout", "Compile/profile dataset & generate Analytical Recipe Catalog"),
            ("memory", "Persist recipe catalog to session context"),
        ],
        "predict": [
            ("scout", "Compile/profile dataset & generate Analytical Recipe Catalog"),
            ("memory", "Persist recipe catalog to session context"),
        ],
        "query_status": [
            ("memory", "Retrieve last session run status/metrics"),
        ],
    }

    _FALLBACK_TEMPLATE: List[tuple] = [
        ("scout", "General discovery — inspect available data sources & build Recipe Catalog"),
        ("memory", "Persist initial discovery to session context"),
    ]

    def get_plan(self, intent: str) -> List[Dict[str, Any]]:
        """Return ordered raw step dicts for the given primary_intent. Never returns an empty list."""
        template = self._PLAN_TEMPLATES.get(intent, self._FALLBACK_TEMPLATE)
        return [
            {"step_id": f"step_{i + 1}", "target_agent": agent, "task": task}
            for i, (agent, task) in enumerate(template)
        ]

    def get_platform_steps(self, recipe_task: str, recipe_title: str) -> List[Dict[str, Any]]:
        """
        Build Platform Agent plan steps dynamically AFTER the user picks a recipe.
        Called by the system after HITL completes, not by the initial Planner run.

        Args:
            recipe_task: REGRESSION | FORECAST | ANOMALY | CLASSIFICATION | HYBRID
            recipe_title: Human-readable recipe title (for logging/display)
        """
        task_map = {
            "REGRESSION": [
                ("platform", f"Feature engineering for '{recipe_title}'"),
                ("platform", f"Train regression candidates for '{recipe_title}'"),
                ("platform", f"Evaluate & select best model for '{recipe_title}'"),
                ("memory", "Persist model leaderboard and selection result"),
            ],
            "FORECAST": [
                ("platform", f"Feature engineering (time-series) for '{recipe_title}'"),
                ("platform", f"Train temporal forecast model for '{recipe_title}'"),
                ("platform", f"Evaluate & select best forecast model for '{recipe_title}'"),
                ("memory", "Persist forecast model result"),
            ],
            "ANOMALY": [
                ("platform", f"Unsupervised anomaly detection pipeline for '{recipe_title}'"),
                ("platform", f"Calibrate anomaly threshold for '{recipe_title}'"),
                ("memory", "Persist anomaly model result"),
            ],
        }
        steps_raw = task_map.get(recipe_task, task_map["REGRESSION"])
        return [
            {"step_id": f"platform_step_{i + 1}", "target_agent": agent, "task": task}
            for i, (agent, task) in enumerate(steps_raw)
        ]

