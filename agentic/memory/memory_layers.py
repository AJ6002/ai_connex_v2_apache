"""
aiconnex_agent/memory/memory_layers.py
========================================
Pydantic contracts for the 4 memory products materialized from the event log.
Kept as 4 separate, typed products (not one generic "searchable memory") so
each has a clear purpose and query pattern:

  - SessionMemory    - current run only, short-lived.
  - EntityMemory      - facts about datasets, users, assets, model branches.
  - ProceduralMemory - what worked/failed, recommended playbooks.
  - DecisionMemory    - HITL answers, overrides, approvals, branch choices.

MemoryBank aggregates all 4 and serializes to a plain dict via to_context(),
so it drops directly into MasterAgentState.memory_context without any state
schema migration. Zero LLM calls, zero I/O - pure data contracts.
"""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class SessionMemory(BaseModel):
    """Current-run snapshot only. Short-lived; not meant to persist across sessions."""
    workflow_id: str = Field(..., description="Correlates to the graph run this snapshot belongs to")
    last_intent: str = Field(default="general", description="Most recent primary_intent for this run")
    steps_run: List[str] = Field(default_factory=list, description="Ordered list of event_types recorded this run")
    status: str = Field(default="running", description="running | complete | failed")


class EntityMemory(BaseModel):
    """Accumulated facts about one dataset/model/asset, keyed by subject_id."""
    subject_id: str = Field(..., description="Identifier of the dataset/model/asset")
    subject_type: str = Field(..., description="dataset | model | asset")
    observations: List[Dict[str, Any]] = Field(default_factory=list, description="Accumulated fact snapshots over time")


class ProceduralMemory(BaseModel):
    """What worked or failed, aggregated by (pattern, outcome) to avoid duplicate noise."""
    pattern: str = Field(..., description="Identifying pattern, e.g. event_type or failure signature")
    outcome: str = Field(..., description="success | failure")
    occurrences: int = Field(default=1, description="Number of times this pattern/outcome combination occurred")


class DecisionMemory(BaseModel):
    """One recorded HITL answer, override, approval, or branch choice."""
    decision_id: str = Field(..., description="Unique decision identifier")
    question: str = Field(default="", description="What was asked")
    answer: Any = Field(default=None, description="What the user/agent decided")
    workflow_id: str = Field(..., description="Correlates to the run this decision was made in")


class MemoryBank(BaseModel):
    """Aggregate of all 4 memory products, materialized by MemoryBuilder from the event log."""
    session: Dict[str, SessionMemory] = Field(default_factory=dict, description="Keyed by workflow_id")
    entities: Dict[str, EntityMemory] = Field(default_factory=dict, description="Keyed by subject_id")
    procedures: List[ProceduralMemory] = Field(default_factory=list)
    decisions: List[DecisionMemory] = Field(default_factory=list)

    def to_context(self) -> Dict[str, Any]:
        """Serialize to a plain JSON-serializable dict for MasterAgentState.memory_context."""
        return {
            "session": {k: v.model_dump() for k, v in self.session.items()},
            "entities": {k: v.model_dump() for k, v in self.entities.items()},
            "procedures": [p.model_dump() for p in self.procedures],
            "decisions": [d.model_dump() for d in self.decisions],
        }
