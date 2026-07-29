"""
aiconnex_agent/memory/events.py
================================
Event taxonomy for the event-sourced Memory Agent. Every domain occurrence
(conversation parsed, dataset compiled, model trained, HITL decision, etc.)
is recorded as a BaseEvent. This module is pure data + a factory function -
zero LLM calls, zero I/O, zero network. See docs/superpowers/plans/
2026-07-29-phase5a-memory-agent.md for the full event family taxonomy.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field

Outcome = Literal["success", "failure", "pending"]


class BaseEvent(BaseModel):
    """A single immutable, auditable domain occurrence."""
    event_id: str = Field(..., description="Unique event identifier, e.g. evt_a1b2c3d4")
    event_type: str = Field(..., description="e.g. DatasetCompiled, ModelTrained, ClarificationAnswered")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    workflow_id: str = Field(..., description="Correlates events belonging to the same graph run/session")
    agent: str = Field(..., description="Emitting agent/node name, e.g. scout, platform, memory, parser")
    subject_type: str = Field(..., description="dataset | model | conversation | plan | decision")
    subject_id: str = Field(..., description="Identifier of the thing this event is about")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific structured data")
    outcome: Outcome = Field(default="success", description="success | failure | pending")


def make_event(
    event_type: str,
    workflow_id: str,
    agent: str,
    subject_type: str,
    subject_id: str,
    payload: Dict[str, Any],
    outcome: Outcome = "success",
) -> BaseEvent:
    """Factory: builds a BaseEvent with an auto-generated id and timestamp."""
    return BaseEvent(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        workflow_id=workflow_id,
        agent=agent,
        subject_type=subject_type,
        subject_id=subject_id,
        payload=payload,
        outcome=outcome,
    )
