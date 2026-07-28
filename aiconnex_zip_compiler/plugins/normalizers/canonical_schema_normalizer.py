"""
plugins/normalizers/canonical_schema_normalizer.py - Canonical Schema & Timestamp Normalizer Plugin
===================================================================================================
Stage 5 Normalizer plugin that standardizes column header names, parses timestamp formats,
and ensures canonical alignment for downstream ML Node 1. Refactored from schema_mapper.py.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional
import pandas as pd

from ..base import BaseSchemaNormalizerPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


TIMESTAMP_PATTERNS = re.compile(
    r"(time|date|datetime|timestamp|time_stamp|date_time|ts|clock|period|year)",
    re.IGNORECASE,
)


@register_plugin
class CanonicalSchemaNormalizerPlugin(BaseSchemaNormalizerPlugin):
    plugin_id = "canonical_schema_normalizer"
    plugin_name = "Canonical Schema & Timestamp Normalizer Plugin"
    version = "2.0.0"
    priority = 10  # Base normalizer

    def probe(self, context: PipelineContext) -> MatchResult:
        if context.assembled_tables or context.harvested_tables or context.parsed_tables:
            return MatchResult(
                supported=True,
                confidence=0.99,
                reasons=["DataFrames available for schema and timestamp normalization"],
                detected_family="canonical_normalizer",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No DataFrames available for normalization"])

    def normalize(self, df: pd.DataFrame, context: PipelineContext) -> pd.DataFrame:
        if df.empty:
            return df

        df_out = df.copy()

        # Clean column names (strip whitespace, sanitize special chars, lowercase)
        raw_cols = list(df_out.columns)
        base_cols = []
        for col in raw_cols:
            c_str = str(col).strip().replace(" ", "_").replace("-", "_")
            c_str = re.sub(r"[^\w\.]", "", c_str).lower()
            base_cols.append(c_str)

        # Count frequencies of base normalized names to detect collisions
        base_counts: Dict[str, int] = {}
        for b in base_cols:
            base_counts[b] = base_counts.get(b, 0) + 1

        used_counts: Dict[str, int] = {}
        seen_final = set()
        final_cols: List[str] = []

        for raw_col, base in zip(raw_cols, base_cols):
            if base_counts[base] > 1:
                used_counts[base] = used_counts.get(base, 0) + 1
                candidate = f"{base}_{used_counts[base]}"
                warning_msg = (
                    f"Column collision detected for raw header '{raw_col}' "
                    f"mapping to duplicate base '{base}'. Suffix deduplicated to '{candidate}'."
                )
                if hasattr(context, "schema_warnings"):
                    context.schema_warnings.append(warning_msg)
                context.audits.append({"type": "schema_warning", "message": warning_msg})
            else:
                candidate = base

            counter = 1
            unique_candidate = candidate
            while unique_candidate in seen_final:
                unique_candidate = f"{candidate}_{counter}"
                counter += 1
                warning_msg = (
                    f"Column collision guard triggered for '{raw_col}'. Renamed to '{unique_candidate}'."
                )
                if hasattr(context, "schema_warnings"):
                    context.schema_warnings.append(warning_msg)
                context.audits.append({"type": "schema_warning", "message": warning_msg})

            seen_final.add(unique_candidate)
            final_cols.append(unique_candidate)

        df_out.columns = final_cols


        # Standardize timestamp column if present
        for col in df_out.columns:
            if TIMESTAMP_PATTERNS.search(col):
                try:
                    df_out[col] = pd.to_datetime(df_out[col], errors="coerce")
                    context.primary_timestamp_col = col
                    break
                except Exception:
                    pass

        return df_out
