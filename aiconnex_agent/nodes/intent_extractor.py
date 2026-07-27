"""
aiconnex_agent/nodes/intent_extractor.py - Node 1: User Intent Extractor
==========================================================================
Uses local Ollama LLM to extract structured UserIntentJSON parameters
(goal, task_type, target_column, domain) from natural language user messages.
Includes deterministic heuristic fallbacks if Ollama is un-reachable.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any
from pathlib import Path

from aiconnex_agent.state import AgentState
from aiconnex_agent.schemas import UserIntentJSON, UploadMetadata
from aiconnex_agent.llm import get_ollama_llm

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are the AIConnex Intent Extraction Agent.
Extract ML intent parameters from the user's input and return ONLY a valid JSON object.

USER INPUT:
"{user_input}"

ZIP FILE PATH:
"{zip_path}"

Return ONLY JSON with these exact keys:
{{
  "user_goal": "<summary of what user wants>",
  "task_type": "<time_series | regression | anomaly | clustering | auto>",
  "target_column": "<column name or null>",
  "domain": "<industrial domain or null>",
  "has_time_series": <true | false>
}}
"""


def _heuristic_intent_extract(user_input: str, zip_path: str, session_id: str) -> UserIntentJSON:
    """Deterministic fallback parser when LLM is offline or returns invalid JSON."""
    inp_lower = user_input.lower()

    task_type = "auto"
    if "forecast" in inp_lower or "time series" in inp_lower or "predict future" in inp_lower:
        task_type = "time_series"
    elif "anomaly" in inp_lower or "outlier" in inp_lower or "fault" in inp_lower:
        task_type = "anomaly"
    elif "cluster" in inp_lower or "group" in inp_lower:
        task_type = "clustering"
    elif "regress" in inp_lower or "predict" in inp_lower:
        task_type = "regression"

    domain = None
    if "compressor" in inp_lower or "gas" in inp_lower or "cng" in inp_lower:
        domain = "CNG Compressor Station"
    elif "solar" in inp_lower or "power" in inp_lower:
        domain = "Solar Generation"
    elif "milling" in inp_lower or "wear" in inp_lower:
        domain = "Milling Manufacturing"

    filename = Path(zip_path).name if zip_path else None

    return UserIntentJSON(
        session_id=session_id,
        user_goal=user_input,
        task_type=task_type,
        domain=domain,
        upload=UploadMetadata(filename=filename, file_type=Path(zip_path).suffix if zip_path else None)
    )


def intent_extractor_node(state: AgentState) -> AgentState:
    """
    Node 1: Parses natural language input into UserIntentJSON slot structure.
    """
    session_id = state.get("session_id", "default_session")
    messages = state.get("messages", [])
    user_msg = messages[-1].content if messages else ""
    zip_path = state.get("zip_path", "")

    existing_intent = state.get("intent", {})
    hitl_answers = existing_intent.get("hitl_answers", {})

    logger.info(f"[IntentExtractorNode] Extracting intent for session '{session_id}' msg='{user_msg}'")

    intent_obj: UserIntentJSON
    try:
        llm = get_ollama_llm(temperature=0.0)
        prompt = EXTRACTION_PROMPT.format(user_input=user_msg, zip_path=zip_path)
        raw_response = llm.invoke(prompt)

        # Parse JSON block from response
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            intent_obj = UserIntentJSON(
                session_id=session_id,
                user_goal=parsed.get("user_goal", user_msg),
                task_type=parsed.get("task_type", "auto"),
                target_column=parsed.get("target_column"),
                domain=parsed.get("domain"),
                upload=UploadMetadata(filename=Path(zip_path).name if zip_path else None),
                hitl_answers=hitl_answers
            )
        else:
            intent_obj = _heuristic_intent_extract(user_msg, zip_path, session_id)
            intent_obj.hitl_answers = hitl_answers
    except Exception as e:
        logger.warning(f"[IntentExtractorNode] LLM extraction failed ({e}). Using heuristic fallback.")
        intent_obj = _heuristic_intent_extract(user_msg, zip_path, session_id)
        intent_obj.hitl_answers = hitl_answers

    # Merge answers if user provided HITL responses
    if messages and "Q" in user_msg and ":" in user_msg:
        # User provided an answer format like "Q1: Sheet 1"
        key, val = user_msg.split(":", 1)
        intent_obj.hitl_answers[key.strip()] = val.strip()

    state["intent"] = intent_obj.model_dump()
    state["stage"] = "intent_extracted"
    return state
