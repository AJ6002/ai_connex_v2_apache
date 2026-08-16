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
    """Delegates to the real multi-candidate Platform Agent Node (Phase 5c)."""
    from aiconnex_agent.platform.platform_node import real_platform_agent_node
    return real_platform_agent_node(state)



def stub_memory_agent_node(state: MasterAgentState) -> Dict[str, Any]:
    """Delegates to the real event-sourced Memory Agent Node."""
    from aiconnex_agent.memory.memory_agent import real_memory_agent_node
    return real_memory_agent_node(state)


def stub_plan_evaluator_node(state: MasterAgentState) -> Dict[str, Any]:
    """Delegates to the real Plan Evaluator Node."""
    from aiconnex_agent.nodes.plan_evaluator import real_plan_evaluator_node
    return real_plan_evaluator_node(state)

