"""
aiconnex_agent/parser/clarification_generator.py
=================================================
Sub-module 6: Generates targeted clarification questions when confidence < 0.85.
"""

from __future__ import annotations
from typing import List
from aiconnex_agent.schemas import ConversationUnderstandingContract


class ClarificationGenerator:
    """Generates clarification question strings for low-confidence prompts."""

    def generate(self, cuc: ConversationUnderstandingContract) -> List[str]:
        """Generate questions based on missing or ambiguous contract fields."""
        intent = cuc.goal.get("primary_intent", "general")
        files = cuc.observed.get("mentioned_files", [])
        questions = []
        
        if not files:
            questions.append("Which dataset file or archive would you like to process?")
        if intent == "general":
            questions.append("Would you like to compile a raw dataset, train an ML model, or run anomaly detection?")
            
        return questions or ["Could you please specify your dataset or project goal?"]
