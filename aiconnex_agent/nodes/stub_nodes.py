"""
aiconnex_agent/nodes/stub_nodes.py - Deterministic Stub Nodes for Phase 1
==========================================================================
Provides lightweight, deterministic stub nodes for building and validating the
LangGraph StateGraph topology without LLM runtime overhead.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

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
    """Delegates to the real ClarificationGenerator-backed Clarification Node."""
    from aiconnex_agent.parser.clarification_node import real_clarification_node
    return real_clarification_node(state)


def stub_planning_engine_node(state: MasterAgentState) -> Dict[str, Any]:
    """Delegates to the real IntentPlanMapper + PlanValidator Planning Engine Node."""
    from aiconnex_agent.planning.planning_engine import real_planning_engine_node
    return real_planning_engine_node(state)


def stub_scout_agent_node(state: MasterAgentState) -> Dict[str, Any]:
    """Delegates to the real UnifiedCompiler-backed Scout Agent Node (Phase 5b)."""
    from aiconnex_agent.scout.scout_node import real_scout_agent_node
    return real_scout_agent_node(state)


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
    """Delegates to the real event-sourced Memory Agent Node."""
    from aiconnex_agent.memory.memory_agent import real_memory_agent_node
    return real_memory_agent_node(state)


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
