"""
aiconnex_agent/nodes/stub_nodes.py - Deterministic Stub Nodes for Phase 1
==========================================================================
Provides lightweight, deterministic stub nodes for building and validating the
LangGraph StateGraph topology without LLM runtime overhead.
"""

from __future__ import annotations

import logging
from typing import Any, Dict
from langgraph.types import interrupt

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.schemas import (
    ConversationUnderstandingContract,
    ScoutEnrichedContract,
    UploadMetadata,
    ArchiveDiscovery,
    FileInventoryItem,
    ParserSelection,
    PreCompilerContract,
    CompilerRequest,
    DatasetIntelligenceContract,
    DatasetIdentity,
    CompiledDatasetSummary,
)

logger = logging.getLogger(__name__)


def stub_conversation_parser_node(state: MasterAgentState) -> Dict[str, Any]:
    """Delegates to the real 6-module Conversation Parser Node."""
    from aiconnex_agent.parser.conversation_parser import real_conversation_parser_node
    return real_conversation_parser_node(state)



def stub_clarification_node(state: MasterAgentState) -> Dict[str, Any]:
    """Stub Clarification Node using LangGraph interrupt()."""
    logger.info("[StubNode] Executing stub_clarification_node (HITL Interrupt)")
    user_answer = interrupt({
        "question": "Which processing mode would you like?",
        "options": ["Automatic Pipeline", "Interactive Step-by-Step"],
        "reason": "Low parser confidence threshold"
    })
    
    cuc_dict = state.cuc.model_dump() if hasattr(state.cuc, "model_dump") else state.cuc.dict()
    cuc_dict["planning_hints"] = {"user_choice": user_answer}
    return {
        "cuc": cuc_dict,
        "active_agent": "planner",
        "confidence_score": 1.0,
    }


def stub_planning_engine_node(state: MasterAgentState) -> Dict[str, Any]:
    """Stub Planning Engine Node."""
    logger.info("[StubNode] Executing stub_planning_engine_node")
    steps = [
        {"step_id": "step_1", "target_agent": "scout", "task": "Discover and parse archive"},
        {"step_id": "step_2", "target_agent": "platform", "task": "Train ML model"},
        {"step_id": "step_3", "target_agent": "memory", "task": "Save session memory"},
    ]
    return {
        "plan_steps": steps,
        "current_step_index": 0,
        "active_agent": "scout",
    }


def stub_scout_agent_node(state: MasterAgentState) -> Dict[str, Any]:
    """Stub Scout Agent Node."""
    logger.info("[StubNode] Executing stub_scout_agent_node")
    scout_dict = state.scout_enriched.model_dump() if hasattr(state.scout_enriched, "model_dump") else state.scout_enriched.dict()
    scout_dict["upload"] = {"status": "uploaded", "archive_name": "suyash2.zip", "archive_type": "zip"}
    scout_dict["archive_discovery"] = {"total_files": 4, "files_detected": ["suyash2.csv"]}
    scout_dict["file_inventory"] = [{"filename": "suyash2.csv", "type": "csv", "role": "fact_table"}]
    return {
        "scout_enriched": scout_dict,
        "active_agent": "evaluator",
    }


def stub_platform_agent_node(state: MasterAgentState) -> Dict[str, Any]:
    """Stub Platform Agent Node."""
    logger.info("[StubNode] Executing stub_platform_agent_node")
    dic_dict = state.dic.model_dump() if hasattr(state.dic, "model_dump") else state.dic.dict()
    dic_dict["dataset_identity"] = {"name": "Suyash2 Telemetry", "family": "Compressor SCADA"}
    dic_dict["compiled_dataset"] = {"tables": 1, "rows": 26898, "columns": 253}
    return {
        "dic": dic_dict,
        "active_agent": "evaluator",
    }


def stub_memory_agent_node(state: MasterAgentState) -> Dict[str, Any]:
    """Stub Memory Agent Node."""
    logger.info("[StubNode] Executing stub_memory_agent_node")
    mem_ctx = dict(state.memory_context)
    mem_ctx["last_saved_session"] = "session_stub_101"
    return {
        "memory_context": mem_ctx,
        "active_agent": "evaluator",
    }


def stub_plan_evaluator_node(state: MasterAgentState) -> Dict[str, Any]:
    """Stub Plan Evaluator Node."""
    logger.info("[StubNode] Executing stub_plan_evaluator_node")
    next_idx = state.current_step_index + 1
    more_steps = next_idx < len(state.plan_steps)
    next_agent = state.plan_steps[next_idx]["target_agent"] if more_steps else "complete"
    return {
        "current_step_index": next_idx,
        "active_agent": next_agent,
    }
