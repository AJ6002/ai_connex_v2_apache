"""
aiconnex_agent/parser/context_manager.py
========================================
Sub-module 2: Manages rolling conversation history and entity state.
"""

from __future__ import annotations
from typing import Dict, Any, List


class ContextManager:
    """Tracks active session entities and conversation turns."""

    def update_context(self, user_prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Append prompt to history and produce updated context dict."""
        new_history = list(history)
        new_history.append({"role": "user", "content": user_prompt})
        return {
            "last_user_prompt": user_prompt,
            "history": new_history,
            "turn_count": len(new_history),
        }
