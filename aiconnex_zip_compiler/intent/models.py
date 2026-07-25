"""
intent/models.py - Data Models for the HITL Intent & Dataset Card Layer
========================================================================
Contains all dataclasses for the intent layer:
  - DatasetCard: Structured summary of dataset type, domain, and structure
  - IntentOption: One choice displayed to the user in the terminal prompt
  - CompilationStrategy: Internal compiler instructions derived from user choice
  - IntentDecision: Recorded in lockfile for reproducibility
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DatasetCard:
    """Structured Data Card summarizing dataset type & structure."""

    dataset_name: str  # "NASA C-MAPSS Turbofan"
    domain: str  # "aerospace_predictive_maintenance"
    dataset_type: str  # "multi_operating_condition_time_series"
    entity_keys: List[str] = field(default_factory=list)  # ["unit_id"]
    time_keys: List[str] = field(default_factory=list)  # ["time_cycles"]
    sensor_columns: List[str] = field(default_factory=list)  # ["sensor_1", "sensor_2", ...]
    detected_conditions: List[str] = field(default_factory=list)  # ["FD001", "FD002", ...]
    detected_sheets: List[str] = field(default_factory=list)  # ["DPR Report", "Reco-Inflow"]
    file_count: int = 0
    total_rows_estimate: int = 0
    summary: str = ""  # Plain-language one-liner for the terminal prompt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "domain": self.domain,
            "dataset_type": self.dataset_type,
            "entity_keys": self.entity_keys,
            "time_keys": self.time_keys,
            "sensor_columns": self.sensor_columns[:10],  # Cap for readability
            "detected_conditions": self.detected_conditions,
            "detected_sheets": self.detected_sheets,
            "file_count": self.file_count,
            "total_rows_estimate": self.total_rows_estimate,
            "summary": self.summary,
        }


@dataclass
class IntentOption:
    """One choice displayed in the terminal prompt."""

    option_id: str  # LLM-generated per dataset, or a legacy fixed id
    label: str  # "Predict equipment failure"
    description: str  # "Get alerts before your compressor breaks down"
    is_default: bool = False  # First option is typically default for batch mode
    # Stable machine-selectable alias. LLM-generated option_ids vary between
    # runs, so automation should target output_mode instead.
    output_mode: str = ""  # "single_merged" | "per_partition_batch" | "keep_separate"


@dataclass
class CompilationStrategy:
    """Internal compiler instructions derived from the user's terminal selection."""

    intent_id: str  # LLM-generated option_id, or legacy fixed id
    scope: str = "all"  # "per_condition" | "unified" | "single_asset" | "all"
    condition_filter: Optional[str] = None  # e.g. "FD001", or None for all

    # Internal decisions (user NEVER sees these):
    sheets_to_include: List[str] = field(default_factory=list)
    sheets_to_exclude: List[str] = field(default_factory=list)
    merge_rule: str = "default"  # "keep_separate" | "vertical_stack" | "merge_on_key" | "default"
    target_synthesis: str = "auto"  # LLM-described derivation, or legacy fixed id
    target_column_hint: Optional[str] = None

    # Plugin policy overrides (set by resolver, read by compiler)
    assembler_policy_override: Optional[str] = None

    # Output shaping (drives handoff): how many artifact sets to emit
    output_mode: str = "single_merged"  # "single_merged" | "per_partition_batch" | "keep_separate"
    partition_by: Optional[str] = None  # partition dimension name, plain language
    partitions: List[Dict[str, Any]] = field(default_factory=list)  # [{group_id, group_label, member_tables}]

    # Provenance: set when the strategy came from LLM reasoning rather than fixed rules
    generated_by_llm: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "scope": self.scope,
            "condition_filter": self.condition_filter,
            "sheets_to_include": self.sheets_to_include,
            "sheets_to_exclude": self.sheets_to_exclude,
            "merge_rule": self.merge_rule,
            "target_synthesis": self.target_synthesis,
            "target_column_hint": self.target_column_hint,
            "assembler_policy_override": self.assembler_policy_override,
            "output_mode": self.output_mode,
            "partition_by": self.partition_by,
            "partitions": self.partitions,
            "generated_by_llm": self.generated_by_llm,
        }


@dataclass
class IntentDecision:
    """Recorded in compiler_lock.json for 100% run reproducibility."""

    dataset_name: str
    data_card: Dict[str, Any]
    options_presented: List[Dict[str, str]]
    user_choice: str
    resolved_strategy: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "data_card": self.data_card,
            "options_presented": self.options_presented,
            "user_choice": self.user_choice,
            "resolved_strategy": self.resolved_strategy,
            "timestamp": self.timestamp,
        }
