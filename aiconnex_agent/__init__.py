"""
AI-Connex Agentic Studio Package - Level 5 Jane Copilot & Local LLM Engine.
"""

from aiconnex_agent.jane_copilot import JaneCopilot, MasterAgentState
from aiconnex_agent.local_gguf_client import (
    DeterministicHeuristicEngine,
    LocalGGUFEngine,
)

__all__ = [
    "DeterministicHeuristicEngine",
    "JaneCopilot",
    "LocalGGUFEngine",
    "MasterAgentState",
]
