"""
plugins/parsers/parquet_parser.py — Apache Parquet / Arrow Parser Plugin
========================================================================
Stage 2 Parser plugin for Apache Parquet files (.parquet, .pq).
Refactored from custom_converters/solar_parquet_converter.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


@register_plugin
class ParquetParserPlugin(BaseParserPlugin):
    plugin_id = "parquet_parser"
    plugin_name = "Apache Parquet / Arrow Parser Plugin"
    version = "1.0.0"
    priority = 50

    def probe(self, context: PipelineContext) -> MatchResult:
        pq_files = [item for item in context.inventory if item.format_ext in [".parquet", ".pq"]]
        if pq_files:
            return MatchResult(
                supported=True,
                confidence=0.98,
                reasons=[f"Found {len(pq_files)} Parquet file(s)"],
                detected_family="parquet",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No Parquet files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        try:
            df = pd.read_parquet(filepath)
            return {filepath.stem: df}
        except Exception as e:
            print(f"[ParquetParserPlugin] Failed to read {filepath}: {e}")
            return {}

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext in [".parquet", ".pq"]:
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
