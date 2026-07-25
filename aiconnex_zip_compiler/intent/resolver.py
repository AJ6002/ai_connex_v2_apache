"""
intent/resolver.py — Intent Choice → CompilationStrategy Resolver
==================================================================
Maps the user's TUI selection into a CompilationStrategy that controls
how the assembler, target synthesis, and scope operate internally.

The user never sees merge rules, column selections, or ML parameters.
They just pick an outcome. This module translates that into compiler instructions.
"""

from __future__ import annotations

import logging
from typing import Optional

from .models import CompilationStrategy, DatasetCard

logger = logging.getLogger(__name__)


class IntentResolver:
    """
    Resolves a user's intent choice + DatasetCard into a CompilationStrategy.
    """

    def resolve(
        self,
        choice_id: str,
        card: DatasetCard,
        condition_filter: Optional[str] = None,
    ) -> CompilationStrategy:
        """
        Map user's selected option_id to internal compilation instructions.

        Parameters
        ----------
        choice_id : str
            The option_id the user selected (e.g. "failure_prediction")
        card : DatasetCard
            The generated dataset card (provides structure context)
        condition_filter : str, optional
            If user selected a specific condition (e.g. "FD001")
        """

        # ── Unified all conditions (C-MAPSS combined) ────────────────────────
        if choice_id == "unified_all_conditions":
            return CompilationStrategy(
                intent_id=choice_id,
                scope="unified",
                condition_filter=None,
                sheets_to_include=[],  # Include all
                sheets_to_exclude=[],
                merge_rule="vertical_stack",
                target_synthesis="rul_countdown",
                target_column_hint="RUL",
                assembler_policy_override="vertical_stack_assembler",
            )

        # ── Separate per-condition (C-MAPSS individual) ──────────────────────
        if choice_id == "separate_per_condition":
            return CompilationStrategy(
                intent_id=choice_id,
                scope="per_condition",
                condition_filter=condition_filter,  # May be None (compile all separately)
                sheets_to_include=[],
                sheets_to_exclude=[],
                merge_rule="keep_separate",
                target_synthesis="rul_countdown",
                target_column_hint="RUL",
                assembler_policy_override="relational_join_assembler",
            )

        # ── Failure prediction (general — SCADA, bearings, battery) ──────────
        if choice_id == "failure_prediction":
            strategy = CompilationStrategy(
                intent_id=choice_id,
                scope="single_asset",
                merge_rule="default",
                target_synthesis="rul_countdown",
                target_column_hint="RUL",
            )
            # For multi-sheet SCADA: use only sensor sheet, exclude accounting
            if card.dataset_type == "multi_sheet_workbook" and card.detected_sheets:
                strategy.sheets_to_include = [card.detected_sheets[0]]  # Primary data sheet
                strategy.sheets_to_exclude = card.detected_sheets[1:]
            return strategy

        # ── Anomaly detection ────────────────────────────────────────────────
        if choice_id == "anomaly_detection":
            strategy = CompilationStrategy(
                intent_id=choice_id,
                scope="single_asset" if card.dataset_type == "multi_sheet_workbook" else "all",
                merge_rule="default",
                target_synthesis="anomaly_flag",
                target_column_hint="is_anomaly",
            )
            if card.dataset_type == "multi_sheet_workbook" and card.detected_sheets:
                strategy.sheets_to_include = [card.detected_sheets[0]]
                strategy.sheets_to_exclude = card.detected_sheets[1:]
            return strategy

        # ── Forecasting (time-series prediction) ─────────────────────────────
        if choice_id == "forecasting":
            strategy = CompilationStrategy(
                intent_id=choice_id,
                scope="all",
                merge_rule="merge_on_key",
                target_synthesis="forecast_horizon",
                target_column_hint=None,  # Will be auto-detected by profiler
                assembler_policy_override="relational_join_assembler",
            )
            return strategy

        # ── Primary sheet model (multi-sheet, use first sheet only) ──────────
        if choice_id == "primary_sheet_model":
            return CompilationStrategy(
                intent_id=choice_id,
                scope="single_asset",
                sheets_to_include=[card.detected_sheets[0]] if card.detected_sheets else [],
                sheets_to_exclude=card.detected_sheets[1:] if len(card.detected_sheets) > 1 else [],
                merge_rule="keep_separate",
                target_synthesis="auto",
            )

        # ── Combined sheets model (merge all on date key) ────────────────────
        if choice_id == "combined_sheets_model":
            return CompilationStrategy(
                intent_id=choice_id,
                scope="all",
                sheets_to_include=card.detected_sheets,
                sheets_to_exclude=[],
                merge_rule="merge_on_key",
                target_synthesis="auto",
                assembler_policy_override="relational_join_assembler",
            )

        # ── Auto model (single table fallback — no user choice needed) ───────
        if choice_id == "auto_model":
            return CompilationStrategy(
                intent_id=choice_id,
                scope="all",
                merge_rule="default",
                target_synthesis="auto",
            )

        # ── Unknown choice — safe fallback ───────────────────────────────────
        logger.warning(f"[IntentResolver] Unknown choice_id '{choice_id}' — using auto strategy")
        return CompilationStrategy(
            intent_id=choice_id,
            scope="all",
            merge_rule="default",
            target_synthesis="auto",
        )
