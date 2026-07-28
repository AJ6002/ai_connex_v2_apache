"""
plugins/parsers/tdms_parser.py - LabVIEW TDMS Telemetry Parser Plugin
========================================================================
Stage 2 Parser plugin for LabVIEW TDMS telemetry files (.tdms).
Ingests binary measurement channels into pandas DataFrames using nptdms,
with graceful degradation if nptdms is not installed.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)


@register_plugin
class TdmsParserPlugin(BaseParserPlugin):
    plugin_id = "tdms_parser"
    plugin_name = "LabVIEW TDMS Telemetry Parser Plugin"
    version = "1.0.0"
    priority = 15

    def probe(self, context: PipelineContext) -> MatchResult:
        tdms_files = [item for item in context.inventory if item.format_ext.lower() == ".tdms"]
        if tdms_files:
            return MatchResult(
                supported=True,
                confidence=0.95,
                reasons=[f"Found {len(tdms_files)} TDMS file(s)"],
                detected_family="tdms",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No TDMS files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        try:
            from nptdms import TdmsFile
        except ImportError:
            logger.warning("[TdmsParserPlugin] nptdms is not installed; skipping TDMS file parsing.")
            return results

        try:
            tdms_file = TdmsFile.read(filepath)
            # Try whole file dataframe conversion first
            if hasattr(tdms_file, "as_dataframe"):
                try:
                    df = tdms_file.as_dataframe()
                    if df is not None and not df.empty:
                        results[filepath.stem] = df
                        return results
                except Exception:
                    pass

            # Fallback to group level extraction
            groups = getattr(tdms_file, "groups", None)
            if groups:
                for group in tdms_file.groups():
                    group_name = getattr(group, "name", "group")
                    if hasattr(group, "as_dataframe"):
                        df_grp = group.as_dataframe()
                        if df_grp is not None and not df_grp.empty:
                            tbl_name = f"{filepath.stem}_{group_name}" if len(tdms_file.groups()) > 1 else filepath.stem
                            results[tbl_name] = df_grp
        except Exception as e:
            logger.warning(f"[TdmsParserPlugin] Failed to read TDMS file {filepath}: {e}")

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext.lower() == ".tdms":
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
