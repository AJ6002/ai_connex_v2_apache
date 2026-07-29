"""
aiconnex_agent/parser/confidence_scorer.py
===========================================
Sub-module 5: Evaluates ambiguity and assigns confidence scores.
"""

from __future__ import annotations
from aiconnex_agent.schemas import ConversationUnderstandingContract


class ConfidenceScorer:
    """Evaluates extraction clarity and computes confidence score [0.0 - 1.0]."""

    def score(self, cuc: ConversationUnderstandingContract) -> float:
        """Compute confidence score based on extracted fields."""
        intent = cuc.goal.get("primary_intent", "general")
        files = cuc.observed.get("mentioned_files", [])
        
        if intent != "general" and files:
            return 0.95
        elif intent != "general":
            return 0.88
        elif files:
            return 0.86
        else:
            return 0.50
