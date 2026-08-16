"""
hitl_schemas.py — Generic, dataset-driven HITL contract (Task 1).

REPLACED (v2, dataset-driven): The prior version hardcoded ETP-domain fields
(operational_goal / primary_parameter / alert_sensitivity / display_format)
that only made sense for one specific test dataset (HTDS-v1.csv wastewater).
This version generalises to any dataset by driving the conversation off the
DIC's actual Recipe Catalog produced by Scout for the file the user uploaded.

  - HITLTurnExtraction: what the LLM returns each turn (structured JSON)
  - HITLContract:        the accumulated state across all HITL turns
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HITLTurnExtraction(BaseModel):
    """Structured output the LLM produces each HITL turn.

    Only fields that changed this turn are populated (same merge pattern as
    pre_upload_flow). `selected_recipe_id` refers to a recipe.id in the DIC's
    Recipe Catalog (e.g. 'R001', 'R002') — NOT a hardcoded ETP goal label.
    """

    # PRIMARY DECISION: which recipe (from dic_context.recipes) did the user pick?
    selected_recipe_id: Optional[str] = Field(
        default=None,
        description="Recipe.id chosen from the DIC's Recipe Catalog this turn (e.g. 'R001')",
    )
    selected_recipe_confidence: float = Field(default=0.0)

    # Free-form dict for recipe-specific follow-up answers the LLM elicits.
    # Example keys the LLM may populate (never hardcoded per domain):
    #   - {"forecast_horizon_days": 7}         for regression/forecasting
    #   - {"alert_sensitivity": "balanced"}    for anomaly detection
    #   - {"display_format": "traffic_light"}  for dashboards
    # The recipe's own task/rationale dictates what follow-ups make sense.
    operational_preferences: Dict[str, Any] = Field(default_factory=dict)

    # Any success criteria the user stated in natural language.
    success_metrics: List[str] = Field(default_factory=list)

    # LLM-generated conversational reply to show the user
    reply: str = Field(default="")

    # True once the LLM has gathered all required fields for the selected recipe
    hitl_complete: bool = Field(default=False)


class HITLContract(BaseModel):
    """Accumulated HITL decision state across all turns."""

    # Primary decision — the recipe from DIC.recipes the user picked
    selected_recipe_id: Optional[str] = None
    selected_recipe_confidence: float = 0.0

    # Recipe-specific follow-up preferences (dataset-agnostic dict, keys chosen by LLM)
    operational_preferences: Dict[str, Any] = Field(default_factory=dict)

    # Success criteria stated by the user
    success_metrics: List[str] = Field(default_factory=list)

    # Derived after recipe selection — resolved from the chosen recipe's own fields
    target_column: Optional[str] = None
    selected_task_family: Optional[str] = None  # regression | anomaly | forecast | hybrid | ...

    # State flags
    hitl_complete: bool = False
    turn_count: int = 0


def _is_complete(contract: HITLContract) -> bool:
    """A contract is complete once the user has picked a recipe with real
    confidence. Recipe-specific follow-up preferences are optional — they
    refine training but do not block completion. This keeps HITL from
    stalling on domain-specific extras that may or may not apply to a given
    dataset; the Workflow Planner / Platform Agent can prompt for missing
    refinements later if needed.
    """
    return bool(contract.selected_recipe_id) and contract.selected_recipe_confidence >= 0.5


def apply_recipe_context(contract: HITLContract, dic_context: dict) -> HITLContract:
    """Once the user has selected a recipe, derive `target_column` and
    `selected_task_family` from the DIC's recipe entry itself — no hardcoded
    ETP mapping. Idempotent: safe to call every turn.
    """
    if not contract.selected_recipe_id:
        return contract

    recipes = dic_context.get("recipes", []) or []
    match = next(
        (r for r in recipes if r.get("id") == contract.selected_recipe_id),
        None,
    )
    if match is None:
        return contract

    contract.target_column = match.get("target") or contract.target_column
    task = match.get("task")
    if isinstance(task, str) and task.strip():
        contract.selected_task_family = task.strip().lower()
    return contract
