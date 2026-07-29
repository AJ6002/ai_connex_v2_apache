"""
aiconnex_agent/parser/semantic_extractor.py
============================================
Sub-module 3: Extracts intent & entities via LLM or deterministic fallback rules.
"""

from __future__ import annotations
import re
from typing import Dict, Any


class SemanticExtractor:
    """Performs semantic extraction using LLM or deterministic heuristics fallback."""

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    def extract(self, user_prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Extract structured dictionary from user prompt."""
        prompt_lower = user_prompt.lower()
        
        # Detect files
        files = re.findall(r'[\w\-\.]+\.(?:zip|csv|xlsx|mat|parquet|tdms|txt)', user_prompt, re.IGNORECASE)
        
        # Detect primary intent
        intent = "general"
        if any(w in prompt_lower for w in ["upload", "compile", "parse", "zip"]):
            intent = "compile_zip"
        elif any(w in prompt_lower for w in ["accuracy", "evaluate", "metrics", "score"]):
            intent = "query_status"
        elif any(w in prompt_lower for w in ["anomaly", "outlier", "isolation forest"]):
            intent = "detect_anomalies"
        elif any(w in prompt_lower for w in ["train", "rul", "regression", "model"]):
            intent = "train_rul"
            
        return {
            "conversation": {"raw_prompt": user_prompt},
            "goal": {"raw_prompt": user_prompt, "primary_intent": intent},
            "observed": {"mentioned_files": files, "mentioned_columns": []},
            "inferred": {"domain": "Industrial Telemetry" if files else None},
            "constraints": {"missing_value_tolerance": 0.2},
            "dataset_expectation": {"expected_format": "zip" if any(f.endswith(".zip") for f in files) else None},
            "clarifications_required": [],
            "planning_hints": {},
        }
