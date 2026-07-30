"""
aiconnex_agent/memory/memory_agent.py
========================================
Real Memory Agent Node orchestrator: Event Store + MemoryPolicyEngine +
MemoryBuilder. Replaces stub_memory_agent_node with real event-sourced
memory, still zero LLM calls (Sprint 1).

Write path (any intent other than query_status): emits the domain events
implied by what upstream nodes already populated on the state (compiled
dataset, trained/evaluated model, the plan that was created, any HITL
decision answered), then rebuilds the MemoryBank from the full event log.

Read path (query_status intent): emits NO new domain events - it only
rebuilds the MemoryBank from whatever is already in the store, so repeated
status queries never inflate the log with duplicate facts.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.memory.events import make_event
from aiconnex_agent.memory.event_store import get_event_store
from aiconnex_agent.memory.policy_engine import MemoryPolicyEngine
from aiconnex_agent.memory.memory_builder import MemoryBuilder
from aiconnex_agent.memory.backends.factory import get_semantic_backend

logger = logging.getLogger(__name__)

_policy = MemoryPolicyEngine()
_builder = MemoryBuilder(_policy)

_MODEL_INTENTS = {"train_rul", "detect_anomalies"}
_DATASET_INTENTS = {"compile_zip", "train_rul", "detect_anomalies"}


def _slugify(name: str, default: str = "unknown_dataset") -> str:
    """Deterministic subject_id from a human-readable dataset name."""
    if not name:
        return default
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"ds_{slug}" if slug else default


def _resolve_workflow_id(state: MasterAgentState) -> str:
    """Bug #2 fix: read state.session_id, which is generated once at state
    construction and survives checkpointer serialization across turns."""
    return state.session_id


def real_memory_agent_node(state: MasterAgentState) -> Dict[str, Any]:
    """Real Memory Agent Node: event-sourced write/read against the EventStore."""
    logger.info("[MemoryAgent] Executing event-sourced memory node")

    store = get_event_store()
    workflow_id = _resolve_workflow_id(state)
    intent = state.cuc.goal.get("primary_intent", "general")

    if intent != "query_status":
        _write_path(store, state, workflow_id, intent)

    bank = _builder.build(store.all())

    mem_ctx = dict(state.memory_context)
    mem_ctx["memory_bank"] = bank.to_context()
    mem_ctx["last_saved_session"] = workflow_id
    mem_ctx["semantic_hits"] = _read_semantic_hits(state, intent)

    return {
        "memory_context": mem_ctx,
        "active_agent": "evaluator",
    }


def _read_semantic_hits(state: MasterAgentState, intent: str) -> list:
    """Fuzzy cross-session recall for query_status only. Never touches Decision/Procedural
    memory - it searches the same SemanticMemoryBackend that memory_builder.py mirrors
    Entity-layer facts into (Phase 5a.6). Kept in its own memory_context key, never merged
    into memory_bank, to preserve the deterministic/fuzzy separation."""
    if intent != "query_status" or not state.messages:
        return []

    query_text = state.messages[-1].get("content", "")
    if not query_text:
        return []

    backend = get_semantic_backend()
    return backend.search(query_text, limit=5)


def _write_path(store, state: MasterAgentState, workflow_id: str, intent: str) -> None:
    """Emit the domain events implied by the current state onto the log."""
    store.append(
        make_event(
            event_type="ConversationParsed",
            workflow_id=workflow_id,
            agent="memory",
            subject_type="conversation",
            subject_id=workflow_id,
            payload={"intent": intent},
        )
    )

    if state.plan_steps:
        store.append(
            make_event(
                event_type="PlanCreated",
                workflow_id=workflow_id,
                agent="memory",
                subject_type="plan",
                subject_id=workflow_id,
                payload={"steps": len(state.plan_steps)},
            )
        )

    user_choice = state.cuc.planning_hints.get("user_choice") if state.cuc.planning_hints else None
    if user_choice is not None:
        store.append(
            make_event(
                event_type="ClarificationAnswered",
                workflow_id=workflow_id,
                agent="memory",
                subject_type="decision",
                subject_id=workflow_id,
                payload={"question": "processing_mode", "answer": user_choice},
            )
        )

    dataset_subject_id = _slugify(state.dic.dataset_identity.name)

    if intent in _DATASET_INTENTS and state.dic.compiled_dataset.rows > 0:
        store.append(
            make_event(
                event_type="DatasetCompiled",
                workflow_id=workflow_id,
                agent="memory",
                subject_type="dataset",
                subject_id=dataset_subject_id,
                payload={
                    "name": state.dic.dataset_identity.name,
                    "family": state.dic.dataset_identity.family,
                    "rows": state.dic.compiled_dataset.rows,
                    "columns": state.dic.compiled_dataset.columns,
                    "tables": state.dic.compiled_dataset.tables,
                },
            )
        )

    if intent in _MODEL_INTENTS:
        model_subject_id = f"model_{dataset_subject_id}"
        store.append(
            make_event(
                event_type="ModelTrained",
                workflow_id=workflow_id,
                agent="memory",
                subject_type="model",
                subject_id=model_subject_id,
                payload={"intent": intent, "dataset": dataset_subject_id},
            )
        )
        store.append(
            make_event(
                event_type="ModelEvaluated",
                workflow_id=workflow_id,
                agent="memory",
                subject_type="model",
                subject_id=model_subject_id,
                payload={"intent": intent, "dataset": dataset_subject_id},
            )
        )
