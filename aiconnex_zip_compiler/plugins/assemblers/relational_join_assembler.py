"""
plugins/assemblers/relational_join_assembler.py - Relational & Index-Join Assembler Plugin
=============================================================================================
Stage 3 Assembler plugin that merges multi-table fact/dimension DataFrames on shared keys
(or index alignment). Implements Cartesian Explosion Guard (<=5% row delta) and automatic
RUL countdown target synthesis for prognostics datasets.

Refactored from monolithic relational_joiner.py.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
import numpy as np

from ..base import BaseAssemblerPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)

# Maximum allowed row growth during a join (5% tolerance)
CARTESIAN_EXPLOSION_THRESHOLD = 1.05


@register_plugin
class RelationalJoinAssemblerPlugin(BaseAssemblerPlugin):
    plugin_id = "relational_join_assembler"
    plugin_name = "Relational & Index-Join Assembler Plugin"
    version = "1.1.0"
    priority = 50

    def probe(self, context: PipelineContext) -> MatchResult:
        if len(context.parsed_tables) >= 2:
            return MatchResult(
                supported=True,
                confidence=0.90,
                reasons=[f"Multiple parsed tables ({len(context.parsed_tables)}) available for assembly"],
                detected_family="multi_table_relational",
            )
        elif len(context.parsed_tables) == 1:
            return MatchResult(
                supported=True,
                confidence=0.75,
                reasons=["Single parsed table available (pass-through assembly)"],
                detected_family="single_table",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No parsed tables available for assembly"])

    def assemble(self, parsed_tables: Dict[str, pd.DataFrame], context: PipelineContext) -> Dict[str, pd.DataFrame]:
        if not parsed_tables:
            return {}

        # -- Apply CompilationStrategy filtering (HITL Intent Layer) ----------
        tables_to_use = self._apply_strategy_filter(parsed_tables, context)

        if not tables_to_use:
            return {}

        if len(tables_to_use) == 1:
            name, df = next(iter(tables_to_use.items()))
            df = self._synthesize_rul(df)
            return {name: df}

        # Check if strategy says keep_separate
        strategy = context.strategy
        if strategy and strategy.merge_rule == "keep_separate":
            # Return each table individually with RUL synthesis applied
            result = {}
            for name, df in tables_to_use.items():
                result[name] = self._synthesize_rul(df)
            return result

        # Multi-table assembly logic
        table_items = list(tables_to_use.items())
        primary_name, primary_df = max(table_items, key=lambda x: len(x[1]))
        merged_df = primary_df.copy()
        fact_rows_before = len(merged_df)

        for name, df in table_items:
            if name == primary_name or df.empty:
                continue

            # Deduplicate dimension table columns that are entity keys not useful as features
            dim_entity_cols = [
                c for c in df.columns
                if ("key" in c.lower() or "source" in c.lower())
                and c.lower() not in [k.lower() for k in self._find_join_keys(merged_df, df)]
            ]
            df_clean = df.drop(columns=dim_entity_cols, errors="ignore")

            # Find common join keys
            join_keys = self._find_join_keys(merged_df, df_clean)

            # Case A: Shared key join
            if join_keys:
                # Deduplicate dimension on join keys before merge
                df_deduped = df_clean.drop_duplicates(subset=join_keys)

                merged_df = merged_df.merge(
                    df_deduped,
                    on=join_keys,
                    how="left",
                    suffixes=("", f"_{name}"),
                )

                # -- Cartesian Explosion Guard --------------------------------
                merged_rows_after = len(merged_df)
                if merged_rows_after > int(fact_rows_before * CARTESIAN_EXPLOSION_THRESHOLD):
                    raise RuntimeError(
                        f"Cartesian Explosion Guard triggered: Row count exploded from "
                        f"{fact_rows_before} to {merged_rows_after} after joining '{name}'. "
                        f"Verify join keys: {join_keys}."
                    )

            # Case B: Equal row count index alignment (parallel sensor channels)
            elif len(df_clean) == len(merged_df):
                new_cols = [c for c in df_clean.columns if c not in merged_df.columns]
                if new_cols:
                    merged_df = pd.concat(
                        [merged_df.reset_index(drop=True), df_clean[new_cols].reset_index(drop=True)],
                        axis=1,
                    )
                logger.debug(f"[RelationalJoinAssembler] Index-aligned '{name}' (equal row count: {len(df_clean)})")

            else:
                logger.warning(
                    f"[RelationalJoinAssembler] Skipped '{name}': No matching join keys and row counts differ "
                    f"({len(df_clean)} vs {len(merged_df)})"
                )

        # -- RUL Countdown Synthesis ------------------------------------------
        merged_df = self._synthesize_rul(merged_df)

        assembled_key = f"{primary_name}_assembled"
        return {assembled_key: merged_df}

    def _find_join_keys(self, left: pd.DataFrame, right: pd.DataFrame) -> List[str]:
        """Find common columns that serve as join keys (timestamp, entity, or explicit keys)."""
        common = list(set(left.columns).intersection(set(right.columns)))
        if not common:
            return []

        # Prefer timestamp and entity columns as join keys
        priority_patterns = re.compile(
            r"(date|time|timestamp|plant_id|unit_id|device_id|asset_id|group_id|entity_id|machine_id)",
            re.IGNORECASE,
        )
        priority_keys = [c for c in common if priority_patterns.search(c)]
        if priority_keys:
            return priority_keys

        # Fall back to first common column
        return [common[0]]

    def _synthesize_rul(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Synthesize piecewise-linear RUL countdown target if unit_id and cycle columns exist.
        RUL = min(125, max_cycle_per_unit - current_cycle)
        """
        if df.empty:
            return df

        # Check if RUL already exists
        rul_cols = [c for c in df.columns if c.lower() == "rul"]
        if rul_cols:
            return df

        # Find unit and cycle columns
        unit_col = next(
            (c for c in df.columns if c.lower() in ("unit_id", "unit", "engine_id", "asset_id")),
            None,
        )
        cycle_col = next(
            (c for c in df.columns if c.lower() in ("cycle", "time_cycles", "flight_cycle", "cycle_id")),
            None,
        )

        if unit_col and cycle_col:
            try:
                max_cycle = df.groupby(unit_col)[cycle_col].transform("max")
                rul = (max_cycle - df[cycle_col]).clip(upper=125).astype(int)
                cycle_idx = df.columns.get_loc(cycle_col)
                df = df.copy()
                df.insert(cycle_idx + 1, "RUL", rul)
                logger.info(
                    f"[RelationalJoinAssembler] Synthesized RUL target (piecewise linear, max_clip=125) "
                    f"from '{unit_col}' + '{cycle_col}'"
                )
            except Exception as e:
                logger.warning(f"[RelationalJoinAssembler] RUL synthesis failed: {e}")

        return df

    def _apply_strategy_filter(
        self, parsed_tables: Dict[str, pd.DataFrame], context: PipelineContext
    ) -> Dict[str, pd.DataFrame]:
        """
        Filter parsed tables based on CompilationStrategy from the HITL Intent Layer.
        If no strategy is set, returns all tables (default behavior).
        """
        strategy = context.strategy
        if not strategy:
            return parsed_tables

        filtered = dict(parsed_tables)

        # Filter by sheets_to_include (if specified, only keep matching tables)
        if strategy.sheets_to_include:
            include_lower = [s.lower().replace(" ", "_") for s in strategy.sheets_to_include]
            filtered = {
                k: v for k, v in filtered.items()
                if any(inc in k.lower() for inc in include_lower)
            }
            # Fallback: if filter excluded everything, use all tables
            if not filtered:
                logger.warning("[Assembler] Strategy include filter matched nothing - using all tables")
                filtered = dict(parsed_tables)

        # Filter by sheets_to_exclude
        if strategy.sheets_to_exclude:
            exclude_lower = [s.lower().replace(" ", "_") for s in strategy.sheets_to_exclude]
            filtered = {
                k: v for k, v in filtered.items()
                if not any(exc in k.lower() for exc in exclude_lower)
            }

        # Filter by condition_filter (e.g. "FD001" - only keep tables with that condition in name)
        if strategy.condition_filter:
            cond = strategy.condition_filter.lower()
            cond_filtered = {
                k: v for k, v in filtered.items()
                if cond in k.lower()
            }
            if cond_filtered:
                filtered = cond_filtered

        return filtered
