"""
aiconnex_agent/nodes/compiler_node.py - Node 2: Dataset Compiler Execution Node
================================================================================
Invokes CompilerAdapter with state["intent"] and state["zip_path"].
Updates state["compiler_result"] and state["hitl_pending"].
"""

from __future__ import annotations

import logging
from pathlib import Path
from aiconnex_agent.state import AgentState
from aiconnex_agent.schemas import UserIntentJSON, CompilerOutputJSON
from aiconnex_agent.compiler_adapter import CompilerAdapter

logger = logging.getLogger(__name__)


def compiler_node(state: AgentState) -> AgentState:
    """
    Node 2: Executes CompilerAdapter. Decides whether to proceed or trigger HITL.
    """
    session_id = state.get("session_id", "default_session")
    zip_path = state.get("zip_path", "")
    intent_dict = state.get("intent", {})

    logger.info(f"[CompilerNode] Running CompilerAdapter for session '{session_id}' zip='{zip_path}'")

    intent_obj = UserIntentJSON(**intent_dict) if intent_dict else UserIntentJSON(session_id=session_id, user_goal="default")
    adapter = CompilerAdapter()

    compiler_out: CompilerOutputJSON = adapter.execute(zip_path=Path(zip_path), intent=intent_obj)
    out_dict = compiler_out.model_dump()

    state["compiler_result"] = out_dict

    if compiler_out.hitl_required:
        state["hitl_pending"] = [q.model_dump() for q in compiler_out.hitl_questions]
        state["stage"] = "hitl_required"
        logger.info(f"[CompilerNode] HITL required ({len(compiler_out.hitl_questions)} questions)")
    elif compiler_out.status == "success":
        state["hitl_pending"] = []
        state["stage"] = "compilation_success"
        logger.info(f"[CompilerNode] Compilation successful: {compiler_out.compiled_csv_path}")
    else:
        state["hitl_pending"] = []
        state["stage"] = "compilation_failed"
        state["error"] = compiler_out.error
        logger.error(f"[CompilerNode] Compilation failed: {compiler_out.error}")

    return state
