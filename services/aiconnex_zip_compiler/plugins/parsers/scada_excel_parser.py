"""
plugins/parsers/scada_excel_parser.py - SCADA Multi-Sheet Excel Parser Plugin
==============================================================================
Stage 2 Parser plugin that handles multi-header, multi-sheet SCADA Excel workbooks
(.xlsx, .xls). Refactored from monolithic excel_converter.py.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


def _cell_type_class(val) -> str:
    """Classifies a cell value into a high-level structural type class."""
    if pd.isna(val) or val is None:
        return "null"
    if isinstance(val, (int, float, complex, np.number)):
        return "number"
    if isinstance(val, (pd.Timestamp, datetime.datetime, datetime.date)):
        return "date"
    if isinstance(val, bool):
        return "bool"
    
    s = str(val).strip()
    if not s:
        return "null"
    
    # Check if string date
    if len(s) >= 8 and any(sep in s for sep in ["-", "/", ":", "T"]):
        try:
            pd.to_datetime(s)
            return "date"
        except (ValueError, TypeError):
            pass

    return "text"


def _is_data_row_start(df_raw: pd.DataFrame, idx: int) -> bool:
    """
    Determines if row `idx` is the start of uniform data rows by evaluating structural
    type consistency across columns between row `idx` and subsequent rows.
    Replaces naive digit heuristics (Gap 9 fix).
    """
    total_rows = len(df_raw)
    if idx >= total_rows:
        return False

    row_curr_types = [_cell_type_class(v) for v in df_raw.iloc[idx]]
    non_null_curr = [t for t in row_curr_types if t != "null"]
    if not non_null_curr:
        return False

    # Ratio of data cells (number, date, bool) in current row
    data_type_count = sum(1 for t in non_null_curr if t in ("number", "date", "bool"))
    curr_data_ratio = data_type_count / len(non_null_curr)

    # If this is the last row, rely on whether it has data types
    if idx == total_rows - 1:
        return curr_data_ratio >= 0.5

    # Check structural type consistency with next row
    row_next_types = [_cell_type_class(v) for v in df_raw.iloc[idx + 1]]
    
    matches = 0
    compared = 0
    for t1, t2 in zip(row_curr_types, row_next_types):
        if t1 != "null" and t2 != "null":
            compared += 1
            if t1 == t2:
                matches += 1

    consistency_ratio = (matches / compared) if compared > 0 else 0.0

    non_null_next = [t for t in row_next_types if t != "null"]
    next_data_ratio = (sum(1 for t in non_null_next if t in ("number", "date", "bool")) / len(non_null_next)) if non_null_next else 0.0

    # A row is a data row start if:
    # 1. It contains data types AND exhibits high structural type consistency with the next row (>= 70%)
    # 2. OR it has predominant data types (>= 50%) and the next row also has predominant data types (>= 40%)
    if curr_data_ratio > 0.0 and consistency_ratio >= 0.70 and (curr_data_ratio >= 0.3 or next_data_ratio >= 0.3):
        return True

    if curr_data_ratio >= 0.5 and next_data_ratio >= 0.4:
        return True

    return False


@register_plugin
class ScadaExcelParserPlugin(BaseParserPlugin):
    plugin_id = "scada_excel_parser"
    plugin_name = "SCADA Multi-Sheet Excel Parser Plugin"
    version = "1.2.0"
    priority = 80  # High priority to claim Excel workbooks before generic parsers

    def probe(self, context: PipelineContext) -> MatchResult:
        excel_files = [item for item in context.inventory if item.format_ext in [".xlsx", ".xls"]]
        if excel_files:
            return MatchResult(
                supported=True,
                confidence=0.98,
                reasons=[f"Found {len(excel_files)} Excel workbook(s) in inventory"],
                detected_family="excel_scada",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No Excel files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        try:
            excel_file = pd.ExcelFile(filepath)
            for sheet_name in excel_file.sheet_names:
                df_raw = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                if df_raw.empty or df_raw.shape[0] < 2:
                    continue

                # Multi-level header detection using structural type-consistency row scanning
                header_rows = []
                data_start_idx = 0
                for idx in range(len(df_raw)):
                    row = df_raw.iloc[idx]
                    non_null_str = [str(val).strip() for val in row.dropna() if str(val).strip() != ""]
                    if not non_null_str:
                        continue
                    if _is_data_row_start(df_raw, idx):
                        data_start_idx = idx
                        break
                    header_rows.append(idx)
                    if len(header_rows) >= 3:
                        data_start_idx = idx + 1
                        break

                if not header_rows:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                else:
                    headers = df_raw.iloc[header_rows].ffill(axis=1).fillna("")
                    combined_cols = []
                    for col_idx in range(df_raw.shape[1]):
                        col_parts = [str(headers.iloc[row_i, col_idx]).strip() for row_i in range(len(header_rows))]
                        clean_parts = [p for p in col_parts if p and not p.startswith("Unnamed")]
                        col_name = " ".join(dict.fromkeys(clean_parts))
                        combined_cols.append(col_name if col_name else f"col_{col_idx}")

                    df_data = df_raw.iloc[data_start_idx:].copy()
                    df_data.columns = combined_cols
                    df = df_data.dropna(how="all").reset_index(drop=True)

                table_key = f"{filepath.stem}_{sheet_name}".replace(" ", "_")
                results[table_key] = df
        except Exception as e:
            print(f"[ScadaExcelParserPlugin] Error parsing {filepath}: {e}")

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext in [".xlsx", ".xls"]:
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
