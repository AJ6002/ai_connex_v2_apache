"""
hitl_schemas.py — Pydantic contract for the post-upload HITL phase.

Mirrors the pre_upload_schemas.py pattern:
  - HITLTurnExtraction: what the LLM returns each turn (structured JSON)
  - HITLContract: the accumulated state across all HITL turns
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class HITLTurnExtraction(BaseModel):
    """Structured output the LLM produces each HITL turn.
    Only fields that changed this turn are populated (same merge pattern as pre_upload)."""

    # Q1: Primary Operational Goal
    operational_goal: Optional[str] = Field(
        default=None,
        description="regression_forecast | anomaly_alert | hybrid_smart_activate"
    )
    operational_goal_confidence: float = Field(default=0.0)

    # Q2: Chemical Parameter Focus
    primary_parameter: Optional[str] = Field(
        default=None,
        description="TDS | COD | both"
    )
    primary_parameter_confidence: float = Field(default=0.0)

    # Q3: Alert Sensitivity (only if Q1 = anomaly_alert or hybrid)
    alert_sensitivity: Optional[str] = Field(
        default=None,
        description="high | balanced | critical_only"
    )
    alert_sensitivity_confidence: float = Field(default=0.0)

    # Q4: Dashboard Display Format (only if Q1 = regression_forecast)
    display_format: Optional[str] = Field(
        default=None,
        description="exact_number | traffic_light | both"
    )
    display_format_confidence: float = Field(default=0.0)

    # LLM-generated conversational reply to show the user
    reply: str = Field(default="")

    # True when the LLM has gathered all required fields for this path
    hitl_complete: bool = Field(default=False)


class HITLContract(BaseModel):
    """Accumulated HITL decision state across all turns."""

    # Q1
    operational_goal: Optional[str] = None
    operational_goal_confidence: float = 0.0

    # Q2
    primary_parameter: Optional[str] = None
    primary_parameter_confidence: float = 0.0

    # Q3 (only for anomaly / hybrid paths)
    alert_sensitivity: Optional[str] = None
    alert_sensitivity_confidence: float = 0.0

    # Q4 (only for regression forecast path)
    display_format: Optional[str] = None
    display_format_confidence: float = 0.0

    # Derived fields (resolved after all questions answered)
    resolved_dag_pool: List[str] = Field(default_factory=list)
    target_column: Optional[str] = None
    branch_ids: List[str] = Field(default_factory=list)

    # State flags
    hitl_complete: bool = False
    turn_count: int = 0


def resolve_dag_pool(contract: HITLContract) -> HITLContract:
    """DAG pool resolution is owned by Phase 2 Platform Agent (multi_dag_resolver.py).

    HITL only captures the user's selected recipe ID; no static DAG IDs are hardcoded in Phase 1.
    """
    contract.resolved_dag_pool = []
    contract.branch_ids = []
    return contract



def _is_complete(contract: HITLContract) -> bool:
    """Check if all required HITL fields are collected for the chosen path."""
    if not contract.operational_goal or not contract.primary_parameter:
        return False
    if contract.operational_goal == "regression_forecast":
        return contract.display_format is not None
    if contract.operational_goal in ("anomaly_alert", "hybrid_smart_activate"):
        return contract.alert_sensitivity is not None
    return False
