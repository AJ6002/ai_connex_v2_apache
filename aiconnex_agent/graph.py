"""
aiconnex_agent/graph.py - LangGraph StateGraph Topology Builder
================================================================
Assembles the complete LangGraph StateGraph topology with checkpointer and routing edges.

chatbot_5jul changes:
- SqliteSaver replaces MemorySaver (survives Flask debug-mode auto-reloads)
- route_after_parser uses is_manifest_minimally_complete() instead of raw confidence threshold
- advise_upload_node parks the graph when manifest is complete but no file uploaded yet
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.parser.conversation_parser import real_conversation_parser_node as conversation_parser_node
from aiconnex_agent.parser.clarification_node import real_clarification_node as clarification_node
from aiconnex_agent.parser.cuc_completion import is_manifest_minimally_complete
from aiconnex_agent.planning.planning_engine import real_planning_engine_node as planning_engine_node
from aiconnex_agent.scout.scout_node import real_scout_agent_node as scout_agent_node
from aiconnex_agent.platform.platform_node import real_platform_agent_node as platform_agent_node
from aiconnex_agent.memory.memory_agent import real_memory_agent_node as memory_agent_node
from aiconnex_agent.nodes.plan_evaluator import real_plan_evaluator_node as plan_evaluator_node


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def advise_upload_node(state: MasterAgentState) -> dict:
    """Park node: manifest is complete but no file uploaded yet.

    Emits an InterruptPayload with interrupt_type='advise_upload' so the
    frontend SSE adapter renders the 'please upload your dataset' card.
    Once the user uploads a file, /api/upload resumes this thread into Scout.
    """
    from langgraph.types import interrupt
    from aiconnex_agent.schemas import InterruptPayload

    payload = InterruptPayload(
        interrupt_type="advise_upload",
        questions=["Your intent is clear. Please upload your dataset to continue."],
        options=[],
        reason="Manifest complete, awaiting dataset upload",
    )
    interrupt(payload.model_dump())
    return {}  # Graph parks here until /api/upload resumes with upload_path


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_after_parser(state: MasterAgentState) -> str:
    """Conditional Edge: field-driven routing via CUC completion helper.

    - Manifest incomplete  → clarification_node  (loop until filled)
    - Manifest complete + no upload → advise_upload_node (park)
    - Manifest complete + upload present → planning_engine_node → Scout
    """
    if not is_manifest_minimally_complete(state.cuc):
        return "clarification_node"
    if not state.upload_path:
        return "advise_upload_node"
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


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(with_checkpointer: bool = True):
    """Build and compile the master LangGraph StateGraph.

    Args:
        with_checkpointer: If True, attaches a SqliteSaver checkpointer
            (persists threads across Flask auto-reloads). Falls back to
            MemorySaver if SqliteSaver is unavailable.
    """
    workflow = StateGraph(MasterAgentState)

    # --- Nodes ---
    workflow.add_node("conversation_parser_node", conversation_parser_node)
    workflow.add_node("clarification_node", clarification_node)
    workflow.add_node("advise_upload_node", advise_upload_node)
    workflow.add_node("planning_engine_node", planning_engine_node)
    workflow.add_node("scout_agent_node", scout_agent_node)
    workflow.add_node("platform_agent_node", platform_agent_node)
    workflow.add_node("memory_agent_node", memory_agent_node)
    workflow.add_node("plan_evaluator_node", plan_evaluator_node)

    # --- Entry ---
    workflow.add_edge(START, "conversation_parser_node")

    # Explicit path→node mapping is REQUIRED for LangGraph Studio static visualization.
    workflow.add_conditional_edges(
        "conversation_parser_node",
        route_after_parser,
        {
            "clarification_node": "clarification_node",
            "advise_upload_node": "advise_upload_node",
            "planning_engine_node": "planning_engine_node",
        },
    )

    # Clarification loops back to parser until manifest is complete
    workflow.add_edge("clarification_node", "conversation_parser_node")

    # advise_upload parks — graph resumes into planning once upload_path is set
    workflow.add_edge("advise_upload_node", "planning_engine_node")

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
        try:
            # SqliteSaver: persists threads across Flask auto-reloads (debug=True)
            # so Tasks 2-8 don't fight "session not found" phantom bugs.
            # *.db is already in .gitignore.
            _db_dir = os.path.join(
                os.path.dirname(__file__), "..", "chatbot", "backend", "data", "sessions"
            )
            os.makedirs(_db_dir, exist_ok=True)
            _db_path = os.path.join(_db_dir, "agent_checkpoints.sqlite")
            saver = SqliteSaver.from_conn_string(_db_path)
            logger.info(f"[Graph] Compiled with SqliteSaver at {_db_path}")
            return workflow.compile(checkpointer=saver)
        except Exception as exc:
            logger.warning(f"[Graph] SqliteSaver unavailable ({exc}), falling back to MemorySaver.")
            from langgraph.checkpoint.memory import MemorySaver
            return workflow.compile(checkpointer=MemorySaver())
    return workflow.compile()
