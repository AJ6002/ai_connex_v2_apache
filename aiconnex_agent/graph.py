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
from aiconnex_agent.nodes.stub_nodes import (
    stub_conversation_parser_node,
    stub_clarification_node,
    stub_planning_engine_node,
    stub_scout_agent_node,
    stub_platform_agent_node,
    stub_memory_agent_node,
    stub_plan_evaluator_node,
)

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
    """Conditional Edge: Continue plan or terminate graph."""
    if state.current_step_index < len(state.plan_steps):
        return route_agent(state)
    return END


def build_graph():
    """Build and compile the master LangGraph StateGraph."""
    workflow = StateGraph(MasterAgentState)
    
    # Add Nodes
    workflow.add_node("conversation_parser_node", stub_conversation_parser_node)
    workflow.add_node("clarification_node", stub_clarification_node)
    workflow.add_node("planning_engine_node", stub_planning_engine_node)
    workflow.add_node("scout_agent_node", stub_scout_agent_node)
    workflow.add_node("platform_agent_node", stub_platform_agent_node)
    workflow.add_node("memory_agent_node", stub_memory_agent_node)
    workflow.add_node("plan_evaluator_node", stub_plan_evaluator_node)
    
    # Add Edges
    workflow.add_edge(START, "conversation_parser_node")
    workflow.add_conditional_edges("conversation_parser_node", route_after_parser)
    workflow.add_edge("clarification_node", "planning_engine_node")
    
    workflow.add_conditional_edges("planning_engine_node", route_agent, {
        "scout_agent_node": "scout_agent_node",
        "platform_agent_node": "platform_agent_node",
        "memory_agent_node": "memory_agent_node",
        END: END,
    })
    
    workflow.add_edge("scout_agent_node", "plan_evaluator_node")
    workflow.add_edge("platform_agent_node", "plan_evaluator_node")
    workflow.add_edge("memory_agent_node", "plan_evaluator_node")
    
    workflow.add_conditional_edges("plan_evaluator_node", route_after_evaluator, {
        "scout_agent_node": "scout_agent_node",
        "platform_agent_node": "platform_agent_node",
        "memory_agent_node": "memory_agent_node",
        END: END,
    })
    
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)
