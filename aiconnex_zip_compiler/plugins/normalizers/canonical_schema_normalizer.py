"""
plugins/normalizers/canonical_schema_normalizer.py — Canonical Schema & Timestamp Normalizer Plugin
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
        cleaned_cols = []
        for col in df_out.columns:
            c_str = str(col).strip().replace(" ", "_").replace("-", "_")
            c_str = re.sub(r"[^\w\.]", "", c_str).lower()
            cleaned_cols.append(c_str)
        df_out.columns = cleaned_cols

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
