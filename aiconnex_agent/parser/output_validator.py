"""
aiconnex_agent/parser/output_validator.py
==========================================
Sub-module 4: Validates extraction dict against ConversationUnderstandingContract.
"""

from __future__ import annotations
from typing import Dict, Any
from aiconnex_agent.schemas import ConversationUnderstandingContract


class StructuredOutputValidator:
    """Validates raw extraction dicts into strongly-typed Pydantic CUC objects."""

    def validate(self, raw_dict: Dict[str, Any]) -> ConversationUnderstandingContract:
        """Validate raw dictionary into ConversationUnderstandingContract."""
        try:
            return ConversationUnderstandingContract(**raw_dict)
        except Exception:
            return ConversationUnderstandingContract(
                goal=raw_dict.get("goal", {}),
                observed=raw_dict.get("observed", {}),
                inferred=raw_dict.get("inferred", {}),
            )
