"""
aiconnex_agent/graph.py - LangGraph StateGraph Topology Builder
================================================================
Assembles the complete LangGraph StateGraph topology with checkpointer and routing edges.
"""

from __future__ import annotations

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.parser.conversation_parser import real_conversation_parser_node as conversation_parser_node
from aiconnex_agent.parser.clarification_node import real_clarification_node as clarification_node
from aiconnex_agent.planning.planning_engine import real_planning_engine_node as planning_engine_node
from aiconnex_agent.scout.scout_node import real_scout_agent_node as scout_agent_node
from aiconnex_agent.platform.platform_node import real_platform_agent_node as platform_agent_node
from aiconnex_agent.memory.memory_agent import real_memory_agent_node as memory_agent_node
from aiconnex_agent.nodes.stub_nodes import stub_plan_evaluator_node as plan_evaluator_node

logger = logging.getLogger(__name__)


def route_after_parser(state: MasterAgentState) -> str:
    """Conditional Edge: Route based on parser confidence score."""
    if state.confidence_score < 0.85:
        return "clarification_node"
    return "planning_engine_node"


def route_agent(state: MasterAgentState) -> str:
    """Conditional Edge: Route to target agent based on current plan step."""
    if not state.plan_steps or state.current_step_index >= len(state.plan_steps):
        return END

    target = state.plan_steps[state.current_step_index].get("target_agent", "scout")
    if target == "scout":
        return "scout_agent_node"
    elif target == "platform":
        return "platform_agent_node"
    elif target == "memory":
        return "memory_agent_node"
    return "scout_agent_node"


def route_after_evaluator(state: MasterAgentState) -> str:
    """Conditional Edge: Continue plan or terminate graph.
    
    Flattened (not delegating to route_agent) so LangGraph Studio
    can statically resolve all reachable paths from plan_evaluator_node.
    """
    if not state.plan_steps or state.current_step_index >= len(state.plan_steps):
        return END

    target = state.plan_steps[state.current_step_index].get("target_agent", "scout")
    if target == "platform":
        return "platform_agent_node"
    elif target == "memory":
        return "memory_agent_node"
    return "scout_agent_node"


def build_graph(with_checkpointer: bool = True):
    """Build and compile the master LangGraph StateGraph.

    Args:
        with_checkpointer: If True, attaches a local MemorySaver checkpointer.
            Set to False when exporting graph for LangGraph Studio / API server.
    """
    workflow = StateGraph(MasterAgentState)

    # --- Nodes ---
    workflow.add_node("conversation_parser_node", conversation_parser_node)
    workflow.add_node("clarification_node", clarification_node)
    workflow.add_node("planning_engine_node", planning_engine_node)
    workflow.add_node("scout_agent_node", scout_agent_node)
    workflow.add_node("platform_agent_node", platform_agent_node)
    workflow.add_node("memory_agent_node", memory_agent_node)
    workflow.add_node("plan_evaluator_node", plan_evaluator_node)

    # --- Entry ---
    workflow.add_edge(START, "conversation_parser_node")

    # Explicit path→node mapping is REQUIRED for LangGraph Studio to draw
    # edges between nodes during static graph visualization.
    workflow.add_conditional_edges(
        "conversation_parser_node",
        route_after_parser,
        {
            "clarification_node": "clarification_node",
            "planning_engine_node": "planning_engine_node",
        },
    )

    workflow.add_edge("clarification_node", "planning_engine_node")

    workflow.add_conditional_edges(
        "planning_engine_node",
        route_agent,
        {
            "scout_agent_node": "scout_agent_node",
            "platform_agent_node": "platform_agent_node",
            "memory_agent_node": "memory_agent_node",
            END: END,
        },
    )

    workflow.add_edge("scout_agent_node", "plan_evaluator_node")
    workflow.add_edge("platform_agent_node", "plan_evaluator_node")
    workflow.add_edge("memory_agent_node", "plan_evaluator_node")

    workflow.add_conditional_edges(
        "plan_evaluator_node",
        route_after_evaluator,
        {
            "scout_agent_node": "scout_agent_node",
            "platform_agent_node": "platform_agent_node",
            "memory_agent_node": "memory_agent_node",
            END: END,
        },
    )

    if with_checkpointer:
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()
