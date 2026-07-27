"""
aiconnex_agent/nodes/hitl_node.py - Node 3: Human-in-the-Loop Interrupt Node
=============================================================================
Pauses LangGraph execution when HITL clarification is required, surfacing
pending HITLQuestions to the caller/chat UI.
"""

from __future__ import annotations

import logging
from langgraph.types import interrupt
from aiconnex_agent.state import AgentState

logger = logging.getLogger(__name__)


def hitl_node(state: AgentState) -> AgentState:
    """
    Node 3: Triggers LangGraph interrupt with state["hitl_pending"].
    When resumed with user response, merges the answers into state["intent"]["hitl_answers"].
    """
    session_id = state.get("session_id", "default_session")
    hitl_pending = state.get("hitl_pending", [])

    logger.info(f"[HITLNode] Interrupting graph for session '{session_id}' with {len(hitl_pending)} questions")

    # Interrupt graph and yield pending questions to user
    user_response = interrupt({
        "status": "hitl_required",
        "session_id": session_id,
        "questions": hitl_pending
    })

    # Resumed: user_response dict passed back from Command(resume=...)
    logger.info(f"[HITLNode] Graph resumed for session '{session_id}' with user response: {user_response}")

    if isinstance(user_response, dict):
        intent = state.get("intent", {})
        hitl_answers = intent.get("hitl_answers", {})
        hitl_answers.update(user_response)
        intent["hitl_answers"] = hitl_answers
        state["intent"] = intent

    state["hitl_pending"] = []
    state["stage"] = "hitl_resolved"
    return state
