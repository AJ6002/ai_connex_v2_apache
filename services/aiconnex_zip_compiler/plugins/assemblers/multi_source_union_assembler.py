"""
plugins/assemblers/multi_source_union_assembler.py - Multi-Source Union Assembler Plugin
==========================================================================================
Stage 3 Assembler plugin that vertically unions same-schema tabular partitions from
multiple sources, plants, or files while adding source_id provenance tags.
"""

from __future__ import annotations

from typing import Dict, List
import pandas as pd

from ..base import BaseAssemblerPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


@register_plugin
class MultiSourceUnionAssemblerPlugin(BaseAssemblerPlugin):
    plugin_id = "multi_source_union_assembler"
    plugin_name = "Multi-Source Union Assembler Plugin"
    version = "1.0.0"
    stage = "assembler"
    priority = 12

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
            # Check column overlap to verify compatibility for vertical union
            col_sets = [set(df.columns) for df in tables]
            first_set = col_sets[0]
            overlap_ratios = [
                len(s.intersection(first_set)) / max(1, len(first_set))
                for s in col_sets
            ]
            if all(r >= 0.5 for r in overlap_ratios):
                return MatchResult(
                    supported=True,
                    confidence=0.85,
                    reasons=[f"Detected {len(tables)} multi-source partition tables with matching column schemas"],
                    detected_family="multi_source_union",
                )

        return MatchResult(
            supported=False,
            confidence=0.0,
            reasons=["Fewer than 2 matching tabular partitions available for multi-source union"],
        )

    def assemble(self, parsed_tables: Dict[str, pd.DataFrame], context: PipelineContext) -> Dict[str, pd.DataFrame]:
        if context.strategy:
            merge_rule = getattr(context.strategy, "merge_rule", None) or (
                context.strategy.get("merge_rule") if isinstance(context.strategy, dict) else None
            )
            if merge_rule == "keep_separate":
                raise ValueError("Multi-source union assembly is incompatible with strategy merge_rule='keep_separate'")

        valid_items = [(key, df.copy()) for key, df in parsed_tables.items() if not df.empty]
        if not valid_items:
            return {}

        tagged_dfs: List[pd.DataFrame] = []
        for src_key, df in valid_items:
            if "source_id" not in df.columns:
                df["source_id"] = src_key
            else:
                df["source_id"] = df["source_id"].fillna(src_key)
            tagged_dfs.append(df)

        union_df = pd.concat(tagged_dfs, ignore_index=True, axis=0)

        context.audits.append({
            "plugin_id": self.plugin_id,
            "action": "multi_source_union",
            "source_count": len(valid_items),
            "total_rows": len(union_df),
        })

        return {"multi_source_union": union_df}
