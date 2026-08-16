"""
aiconnex_agent/parser/prompt_builder.py
========================================
Sub-module 1: Constructs structured system prompts for LLM semantic extraction.
"""

from __future__ import annotations


class PromptBuilder:
    """Formats raw chat + context into structured prompts for ConversationUnderstandingContract parsing."""

    SYSTEM_INSTRUCTIONS = """You are the AIConnex Conversation Understanding Engine.
Your task is to analyze the user prompt and extract structured intent into a JSON object matching the ConversationUnderstandingContract schema.

Extracted JSON must contain:
- goal: {raw_prompt, primary_intent: "compile_zip"|"train_rul"|"detect_anomalies"|"predict"|"query_status"|"general", task_family: "regression"|"anomaly_detection"|"forecasting"|"classification"|"clustering"|"general", business_goal: string}
- observed: {mentioned_files: [], mentioned_entities: []}
- inferred: {domain: string|null, expected_target: string|null}
- business_context: {industry: string, process: string, asset: string, operational_objective: string}
- constraints: {missing_value_tolerance: float}
- dataset_expectation: {expected_format: "zip"|"csv"|"excel"|"mat"|null, expected_source: "user_statement"|"inferred"}

NOTE on observed.mentioned_entities: extract entities the user names in THEIR
OWN WORDS (e.g. "temperature", "pressure") — do NOT guess or assume these are
literal dataset column names. Actual column names are discovered later by the
Scout agent once the real dataset is uploaded; a user saying "temperature"
does not mean the eventual column will be called that (it could be "Temp_C").
"""

    def build_system_prompt(self, user_prompt: str, context_summary: str = "") -> str:
        """Combine system instructions, context summary, and target user prompt."""
        return f"{self.SYSTEM_INSTRUCTIONS}\nContext: {context_summary}\nUser Prompt: {user_prompt}"
