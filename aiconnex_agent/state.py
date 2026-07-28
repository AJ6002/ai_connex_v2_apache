"""
aiconnex_agent/state.py - LangGraph AgentState TypedDict
=========================================================
State definition tracking session messages, intent JSON, HITL questions,
compiler results, and orchestration stage across graph execution steps.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    session_id: str
    messages: List[BaseMessage]          # Full conversation history
    intent: Dict[str, Any]               # UserIntentJSON dictionary representation
    zip_path: Optional[str]              # Path to input ZIP/dataset file
    hitl_pending: List[Dict[str, Any]]   # Pending HITLQuestion items
    compiler_result: Dict[str, Any]      # CompilerOutputJSON dictionary representation
    pipeline_result: Dict[str, Any]      # 9-node pipeline output representation
    stage: str                           # Current orchestration stage name
    error: Optional[str]                 # Error message string if failed
