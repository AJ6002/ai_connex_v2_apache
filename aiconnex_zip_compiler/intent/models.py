"""
intent/models.py — Data Models for the HITL Intent & Dataset Card Layer
========================================================================
Contains all dataclasses for the intent layer:
  - DatasetCard: Structured summary of dataset type, domain, and structure
  - IntentOption: One choice displayed to the user in the TUI
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
    summary: str = ""  # Plain-language one-liner for the TUI

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
    """One choice displayed in the TUI terminal prompt."""

    option_id: str  # "failure_prediction", "anomaly_detection", "forecasting"
    label: str  # "Predict equipment failure"
    description: str  # "Get alerts before your compressor breaks down"
    icon: str = ""  # "🔧"
    is_default: bool = False  # First option is typically default for batch mode


@dataclass
class CompilationStrategy:
    """Internal compiler instructions derived from the TUI user selection."""

    intent_id: str  # "failure_prediction" | "anomaly_detection" | "forecasting"
    scope: str = "all"  # "per_condition" | "unified" | "single_asset" | "all"
    condition_filter: Optional[str] = None  # "FD001" or None (all)

    # Internal decisions (user NEVER sees these):
    sheets_to_include: List[str] = field(default_factory=list)
    sheets_to_exclude: List[str] = field(default_factory=list)
    merge_rule: str = "default"  # "keep_separate" | "vertical_stack" | "merge_on_key" | "default"
    target_synthesis: str = "auto"  # "rul_countdown" | "anomaly_flag" | "forecast_horizon" | "auto"
    target_column_hint: Optional[str] = None  # "RUL", "is_anomaly", "next_day_pressure"

    # Plugin policy overrides (set by resolver, read by compiler)
    assembler_policy_override: Optional[str] = None  # "relational_join_assembler" | "vertical_stack_assembler"

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
