"""
plugins/parsers/scada_excel_parser.py — SCADA Multi-Sheet Excel Parser Plugin
==============================================================================
Stage 2 Parser plugin that handles multi-header, multi-sheet SCADA Excel workbooks
(.xlsx, .xls). Refactored from monolithic excel_converter.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


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

                # Multi-level header detection
                header_rows = []
                data_start_idx = 0
                for idx, row in df_raw.iterrows():
                    non_null_str = [str(val).strip() for val in row.dropna() if str(val).strip() != ""]
                    if not non_null_str:
                        continue
                    if any(c.replace(".", "").isdigit() for c in non_null_str):
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
