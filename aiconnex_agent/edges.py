"""
aiconnex_agent/edges.py - Conditional Edge Routing Logic for LangGraph
======================================================================
Defines decision functions for routing execution between nodes based on
state["compiler_result"] and state["stage"].
"""

from __future__ import annotations

from typing import Literal
from aiconnex_agent.state import AgentState


def route_after_compiler(state: AgentState) -> Literal["hitl_node", "data_explorer_node", "__end__"]:
    """
    Decides where to route after compiler_node runs:
    - hitl_node if HITL clarification is required
    - data_explorer_node if compilation succeeded
    - __end__ if compilation failed or unsupported format
    """
    stage = state.get("stage")
    if stage == "hitl_required":
        return "hitl_node"
    elif stage == "compilation_success":
        return "data_explorer_node"
    else:
        return "__end__"
