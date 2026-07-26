"""
plugins/assemblers/keyed_time_join_assembler.py - Keyed Time Join Assembler Plugin
====================================================================================
Stage 3 Assembler plugin that executes timestamp-aligned merges and ASOF JOINs
across multi-sensor telemetry tables sharing time and asset keys.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional
import pandas as pd

from ..base import BaseAssemblerPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

TIMESTAMP_PATTERNS = re.compile(
    r"(time|date|datetime|timestamp|time_stamp|date_time|ts|clock)",
    re.IGNORECASE,
)

ASSET_KEY_PATTERNS = re.compile(
    r"(asset_id|device_id|unit_id|entity_id|plant_id|sensor_id|asset|device|unit|entity)",
    re.IGNORECASE,
)


def _find_col(df: pd.DataFrame, pattern: re.Pattern) -> Optional[str]:
    for col in df.columns:
        if pattern.search(str(col)):
            return str(col)
    return None


@register_plugin
class KeyedTimeJoinAssemblerPlugin(BaseAssemblerPlugin):
    plugin_id = "keyed_time_join_assembler"
    plugin_name = "Keyed Time Join Assembler Plugin"
    version = "1.0.0"
    stage = "assembler"
    priority = 15

    def probe(self, context: PipelineContext) -> MatchResult:
        if context.strategy:
            merge_rule = getattr(context.strategy, "merge_rule", None) or (
                context.strategy.get("merge_rule") if isinstance(context.strategy, dict) else None
            )
            if merge_rule == "keep_separate":
                return MatchResult(
                    supported=False,
                    confidence=0.0,
                    reasons=["Compilation strategy explicitly specifies merge_rule='keep_separate'"],
                )

        tables = [df for df in context.parsed_tables.values() if not df.empty]
        if len(tables) >= 2:
            time_cols = [_find_col(df, TIMESTAMP_PATTERNS) for df in tables]
            valid_time_count = sum(1 for tc in time_cols if tc is not None)
            if valid_time_count >= 2:
                has_asset_keys = any(_find_col(df, ASSET_KEY_PATTERNS) is not None for df in tables)
                conf = 0.90 if has_asset_keys else 0.85
                return MatchResult(
                    supported=True,
                    confidence=conf,
                    reasons=[f"Detected {valid_time_count} tables with timestamp columns for time-aligned join"],
                    detected_family="keyed_time_join",
                )

        return MatchResult(
            supported=False,
            confidence=0.0,
            reasons=["Fewer than 2 tables with valid timestamp columns for keyed time join"],
        )

    def assemble(self, parsed_tables: Dict[str, pd.DataFrame], context: PipelineContext) -> Dict[str, pd.DataFrame]:
        if context.strategy:
            merge_rule = getattr(context.strategy, "merge_rule", None) or (
                context.strategy.get("merge_rule") if isinstance(context.strategy, dict) else None
            )
            if merge_rule == "keep_separate":
                raise ValueError("Keyed time join assembly is incompatible with strategy merge_rule='keep_separate'")

        valid_dfs: List[pd.DataFrame] = []
        for df in parsed_tables.values():
            if not df.empty:
                df_copy = df.copy()
                t_col = _find_col(df_copy, TIMESTAMP_PATTERNS)
                if t_col:
                    df_copy[t_col] = pd.to_datetime(df_copy[t_col], errors="coerce")
                    valid_dfs.append(df_copy)

        if not valid_dfs:
            return {}

        if len(valid_dfs) == 1:
            return {"keyed_time_join": valid_dfs[0]}

        # Pick primary time column and asset key column from first table
        base_df = valid_dfs[0]
        primary_time = _find_col(base_df, TIMESTAMP_PATTERNS) or "timestamp"
        primary_key = _find_col(base_df, ASSET_KEY_PATTERNS)

        base_df = base_df.dropna(subset=[primary_time]).sort_values(by=primary_time).reset_index(drop=True)
        merged_df = base_df

        for i, right_df in enumerate(valid_dfs[1:], start=1):
            right_time = _find_col(right_df, TIMESTAMP_PATTERNS) or primary_time
            right_key = _find_col(right_df, ASSET_KEY_PATTERNS)

            # Ensure right_time column matches primary_time name
            if right_time != primary_time:
                right_df = right_df.rename(columns={right_time: primary_time})

            # Ensure right_key column matches primary_key name if both exist
            if primary_key and right_key and right_key != primary_key:
                right_df = right_df.rename(columns={right_key: primary_key})

            right_df = right_df.dropna(subset=[primary_time]).sort_values(by=primary_time).reset_index(drop=True)

            use_by = primary_key if (primary_key and primary_key in merged_df.columns and primary_key in right_df.columns) else None

            try:
                if use_by:
                    merged_df = pd.merge_asof(
                        merged_df,
                        right_df,
                        on=primary_time,
                        by=use_by,
                        direction="nearest",
                        suffixes=("", f"_s{i}")
                    )
                else:
                    merged_df = pd.merge_asof(
                        merged_df,
                        right_df,
                        on=primary_time,
                        direction="nearest",
                        suffixes=("", f"_s{i}")
                    )
            except Exception:
                # Fallback to standard merge if merge_asof fails
                on_cols = [primary_time]
                if use_by:
                    on_cols.append(use_by)
                merged_df = pd.merge(merged_df, right_df, on=on_cols, how="outer", suffixes=("", f"_s{i}"))

        context.audits.append({
            "plugin_id": self.plugin_id,
            "action": "keyed_time_join",
            "table_count": len(valid_dfs),
            "total_rows": len(merged_df),
            "primary_time": primary_time,
            "asset_key": primary_key,
        })

        return {"keyed_time_join": merged_df}
