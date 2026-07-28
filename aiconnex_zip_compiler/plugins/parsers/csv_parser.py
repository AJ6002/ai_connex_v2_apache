"""
plugins/parsers/csv_parser.py - Generic CSV / TXT Parser Plugin
================================================================
Stage 2 Parser plugin for standard CSV and whitespace-delimited TXT files.
Handles:
  - Standard CSV with headers
  - Whitespace-delimited TXT (C-MAPSS, PHM08 pattern)
  - Headerless 26-column turbofan sensor matrices (auto-names: unit_id, cycle, op_setting_1-3, sensor_1-21)
  - Multi-encoding fallback (utf-8, latin-1, utf-8-sig)
  - Multi-separator detection (comma, tab, semicolon, whitespace)

Refactored from monolithic discovery.py:safe_read_csv() implementation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)

# C-MAPSS / PHM08 standard 26-column header assignment
CMAPSS_26_COLUMNS = (
    ["unit_id", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"]
    + [f"sensor_{i}" for i in range(1, 22)]
)


def _is_numeric_header(col_name) -> bool:
    """Return True if column name string parses cleanly to a float (indicates headerless file)."""
    try:
        float(str(col_name).strip())
        return True
    except ValueError:
        return False


@register_plugin
class CsvParserPlugin(BaseParserPlugin):
    plugin_id = "csv_parser"
    plugin_name = "Generic CSV / TXT Parser Plugin"
    version = "1.1.0"
    priority = 10  # Standard priority for general CSV/TXT parsing

    def probe(self, context: PipelineContext) -> MatchResult:
        csv_files = [item for item in context.inventory if item.format_ext in [".csv", ".txt"]]
        if csv_files:
            return MatchResult(
                supported=True,
                confidence=0.95,
                reasons=[f"Found {len(csv_files)} CSV/TXT file(s) in inventory"],
                detected_family="csv",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No CSV or TXT files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        df = self._safe_read_csv(filepath)
        table_name = filepath.stem
        return {table_name: df}

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext in [".csv", ".txt"] and item.detected_role != "snapshot":
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context

    def _safe_read_csv(self, filepath: Path) -> pd.DataFrame:
        """
        Robust CSV/TXT reader handling:
        - Bad lines, comment headers, encoding errors
        - Headerless numeric files (C-MAPSS 26-column auto-naming)
        - Multiple separators and encodings
        """
        is_txt = str(filepath).lower().endswith(".txt")
        separators = [r"\s+", ",", "\t", ";"] if is_txt else [",", r"\s+", "\t", ";"]

        df: Optional[pd.DataFrame] = None

        for enc in ["utf-8", "latin-1", "utf-8-sig"]:
            for sep in separators:
                try:
                    df = pd.read_csv(filepath, on_bad_lines="skip", encoding=enc, sep=sep)
                    if df is not None and not df.empty and df.shape[1] > 1:
                        break
                except Exception:
                    try:
                        df = pd.read_csv(
                            filepath, engine="python", on_bad_lines="skip", encoding=enc, sep=sep
                        )
                        if df is not None and not df.empty and df.shape[1] > 1:
                            break
                    except Exception:
                        continue
            if df is not None and not df.empty and df.shape[1] > 1:
                break

        # Last resort fallback
        if df is None or df.empty:
            try:
                df = pd.read_csv(filepath, engine="python", on_bad_lines="skip", encoding_errors="ignore")
            except Exception:
                df = pd.DataFrame()

        # -- Headerless Detection & C-MAPSS Auto-Naming -----------------------
        if df is not None and not df.empty:
            # Check if ALL column names are numeric (indicates the file has no header row)
            cols_to_check = [str(c).split()[0] for c in df.columns]
            if all(_is_numeric_header(c) for c in cols_to_check):
                try:
                    df_headerless = pd.read_csv(
                        filepath,
                        header=None,
                        engine="python",
                        sep=r"\s+",
                        on_bad_lines="skip",
                        encoding_errors="ignore",
                    )

                    if df_headerless.shape[1] == 26:
                        # C-MAPSS / PHM08 standard turbofan 26-column format
                        df_headerless.columns = CMAPSS_26_COLUMNS
                        logger.info(
                            f"[CsvParser] Detected 26-column headerless file '{filepath.name}' "
                            f"-> assigned C-MAPSS standard column names"
                        )
                    else:
                        # Generic headerless: assign col_0, col_1, ...
                        df_headerless.columns = [f"col_{i}" for i in range(df_headerless.shape[1])]

                    df = df_headerless
                except Exception:
                    pass

        return df if df is not None else pd.DataFrame()
