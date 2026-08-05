"""
aiconnex_agent/parser/clarification_node.py
==============================================
Real Clarification Node: replaces the previously hardcoded stub, which
always asked the same fixed question regardless of what was actually
ambiguous about the request. This node uses the real ClarificationGenerator
(sub-module 6) to compose targeted questions from the actual CUC gaps, then
pauses the graph via LangGraph's interrupt() until the user answers.

chatbot_5jul fix: interrupt() now emits a typed InterruptPayload with
interrupt_type="clarification" so the frontend SSE adapter can distinguish
clarification events from strategy_choice events uniformly.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from langgraph.types import interrupt

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.parser.clarification_generator import ClarificationGenerator
from aiconnex_agent.schemas import InterruptPayload

logger = logging.getLogger(__name__)

# Module singleton, consistent with conversation_parser.py's pattern.
clarification_generator = ClarificationGenerator()


def real_clarification_node(state: MasterAgentState) -> Dict[str, Any]:
    """Real Clarification Node: real, CUC-derived questions instead of a hardcoded one.

    Emits a typed InterruptPayload(interrupt_type='clarification') so the
    frontend SSE adapter and assistant-ui can render clarification questions
    distinctly from strategy_choice interrupts.
    """
    logger.info("[ClarificationNode] Executing real HITL clarification")

    questions = clarification_generator.generate(state.cuc)

    payload = InterruptPayload(
        interrupt_type="clarification",
        questions=questions,
        options=[],
        reason="Parser confidence below 0.85 or required CUC fields missing",
    )

    user_answer = interrupt(payload.model_dump())

    cuc_dict = state.cuc.model_dump() if hasattr(state.cuc, "model_dump") else state.cuc.dict()
    cuc_dict["planning_hints"] = {"user_choice": user_answer}
    return {
        "cuc": cuc_dict,
        "active_agent": "planner",
        "confidence_score": 1.0,
    }
