"""
aiconnex_agent/runner.py - Main Entrypoint for AIConnex LangGraph Agent
========================================================================
Exposes `process(user_message, zip_path, session_id, hitl_answers=None)` to run or resume
the agent workflow across turns.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from aiconnex_agent.graph import aiconnex_graph
from aiconnex_agent.state import AgentState

logger = logging.getLogger(__name__)


def process_agent_request(
    user_message: str,
    zip_path: str,
    session_id: str = "session_001",
    hitl_resume_answers: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Runs or resumes the AIConnex LangGraph agentic pipeline.

    Parameters
    ----------
    user_message : str
        Natural language goal/query from the user.
    zip_path : str
        Path to raw dataset ZIP archive or file.
    session_id : str
        Thread session ID used by MemorySaver checkpointer.
    hitl_resume_answers : dict, optional
        Answers dict when resuming from a HITL interrupt.

    Returns
    -------
    dict
        State dictionary containing compiler_result, hitl_pending, stage, etc.
    """
    config = {"configurable": {"thread_id": session_id}}

    if hitl_resume_answers:
        logger.info(f"[Runner] Resuming session '{session_id}' with HITL answers: {hitl_resume_answers}")
        # Resume graph from interrupt checkpoint
        result_state = aiconnex_graph.invoke(
            Command(resume=hitl_resume_answers),
            config=config
        )
    else:
        logger.info(f"[Runner] Starting new invocation for session '{session_id}' msg='{user_message}'")
        initial_state: AgentState = {
            "session_id": session_id,
            "messages": [HumanMessage(content=user_message)],
            "intent": {},
            "zip_path": zip_path,
            "hitl_pending": [],
            "compiler_result": {},
            "pipeline_result": {},
            "stage": "started",
            "error": None,
        }

        # Check if thread state exists
        try:
            curr_state = aiconnex_graph.get_state(config)
            if curr_state and curr_state.next:
                # Graph was interrupted in previous turn
                logger.info(f"[Runner] Found interrupted thread state. Resuming with user message.")
                result_state = aiconnex_graph.invoke(
                    Command(resume={"user_input": user_message}),
                    config=config
                )
            else:
                result_state = aiconnex_graph.invoke(initial_state, config=config)
        except Exception:
            result_state = aiconnex_graph.invoke(initial_state, config=config)

    return result_state
