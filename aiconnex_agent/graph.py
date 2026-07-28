"""
aiconnex_agent/graph.py - LangGraph StateGraph Definition
===========================================================
Assembles and compiles the AIConnex agentic orchestration graph.
Topology:
  [START] -> intent_extractor -> compiler_node
              |-> hitl_node -> compiler_node
              |-> data_explorer -> scope_narrower -> pipeline_trigger -> [END]
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from aiconnex_agent.state import AgentState
from aiconnex_agent.nodes.intent_extractor import intent_extractor_node
from aiconnex_agent.nodes.compiler_node import compiler_node
from aiconnex_agent.nodes.hitl_node import hitl_node
from aiconnex_agent.nodes.data_explorer import data_explorer_node
from aiconnex_agent.nodes.scope_narrower import scope_narrower_node
from aiconnex_agent.nodes.pipeline_trigger import pipeline_trigger_node
from aiconnex_agent.edges import route_after_compiler


def build_aiconnex_graph():
    """
    Constructs and compiles the AIConnex LangGraph agent graph.
    """
    builder = StateGraph(AgentState)

    # 1. Add Nodes
    builder.add_node("intent_extractor", intent_extractor_node)
    builder.add_node("compiler_node", compiler_node)
    builder.add_node("hitl_node", hitl_node)
    builder.add_node("data_explorer", data_explorer_node)
    builder.add_node("scope_narrower", scope_narrower_node)
    builder.add_node("pipeline_trigger", pipeline_trigger_node)

    # 2. Add Edges
    builder.add_edge(START, "intent_extractor")
    builder.add_edge("intent_extractor", "compiler_node")

    # Conditional edge after compiler_node
    builder.add_conditional_edges(
        "compiler_node",
        route_after_compiler,
        {
            "hitl_node": "hitl_node",
            "data_explorer_node": "data_explorer",
            "__end__": END,
        }
    )

    # After HITL node resolves answers, re-run compiler_node
    builder.add_edge("hitl_node", "compiler_node")

    # Linear flow through remaining stubs
    builder.add_edge("data_explorer", "scope_narrower")
    builder.add_edge("scope_narrower", "pipeline_trigger")
    builder.add_edge("pipeline_trigger", END)

    # Compile graph with MemorySaver checkpointer for stateful HITL interrupts
    checkpointer = MemorySaver()
    compiled_graph = builder.compile(checkpointer=checkpointer)
    return compiled_graph


# Expose default compiled graph instance
aiconnex_graph = build_aiconnex_graph()
