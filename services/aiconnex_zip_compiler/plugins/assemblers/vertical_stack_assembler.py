"""
plugins/assemblers/vertical_stack_assembler.py - Vertical Stacking Assembler Plugin
====================================================================================
Stage 3 Assembler plugin that stacks multiple periodic/monthly tables vertically
when schemas match (e.g. SCADA Excel monthly DPR logs or split CSV chunks).
"""

from __future__ import annotations

from typing import Dict, List
import pandas as pd

from ..base import BaseAssemblerPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


@register_plugin
class VerticalStackAssemblerPlugin(BaseAssemblerPlugin):
    plugin_id = "vertical_stack_assembler"
    plugin_name = "Vertical Stacking Assembler Plugin"
    version = "1.0.0"
    priority = 70  # Higher priority than relational join when schemas match

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

        tables = list(context.parsed_tables.values())
        if len(tables) >= 2:
            # Check if column shapes match across tables
            col_sets = [set(df.columns) for df in tables if not df.empty]
            if len(col_sets) >= 2 and all(len(s.intersection(col_sets[0])) >= max(1, len(col_sets[0]) * 0.7) for s in col_sets):
                return MatchResult(
                    supported=True,
                    confidence=0.92,
                    reasons=[f"Multiple tables with matching schemas detected ({len(col_sets)} tables)"],
                    detected_family="vertical_stack",
                )
        return MatchResult(supported=False, confidence=0.0, reasons=["Tables do not share matching column schemas for vertical stacking"])

    def assemble(self, parsed_tables: Dict[str, pd.DataFrame], context: PipelineContext) -> Dict[str, pd.DataFrame]:
        if context.strategy:
            merge_rule = getattr(context.strategy, "merge_rule", None) or (
                context.strategy.get("merge_rule") if isinstance(context.strategy, dict) else None
            )
            if merge_rule == "keep_separate":
                raise ValueError("Vertical stacking assembly is incompatible with strategy merge_rule='keep_separate'")

        valid_dfs = []
        for df in parsed_tables.values():
            if not df.empty:
                df_copy = df.copy()
                if not df_copy.columns.is_unique:
                    cols = []
                    seen = {}
                    for col in df_copy.columns:
                        col_str = str(col).strip()
                        if col_str in seen:
                            seen[col_str] += 1
                            cols.append(f"{col_str}_{seen[col_str]}")
                        else:
                            seen[col_str] = 0
                            cols.append(col_str)
                    df_copy.columns = cols
                valid_dfs.append(df_copy.reset_index(drop=True))

        if not valid_dfs:
            return {}

        stacked_df = pd.concat(valid_dfs, ignore_index=True, axis=0)
        return {"stacked_dataset": stacked_df}

