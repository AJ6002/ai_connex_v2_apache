"""
plugins/normalizers/unit_standardizer.py - Unit Standardizer Normalizer Plugin
==============================================================================
Stage 5 Normalizer plugin that standardizes physical unit suffixes (psi -> bar, degF -> degC,
kW -> W, mph -> m/s) in numeric columns and converts values using standard engineering factors.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

from ..base import BaseSchemaNormalizerPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


# Engineering conversion rules: (Pattern, Replacement Suffix, Conversion Callable)
UNIT_RULES: List[Tuple[re.Pattern, str, str]] = [
    # PSI -> Bar (1 psi = 0.0689476 bar)
    (re.compile(r"(?i)(_?psi)$"), "bar", "psi_to_bar"),
    # DegF -> DegC ((degF - 32) * 5/9 = degC)
    (re.compile(r"(?i)(_?degf|_?deg_f|_?fahrenheit)$"), "degc", "degf_to_degc"),
    # kW -> W (1 kW = 1000 W)
    (re.compile(r"(?i)(_?kw)$"), "w", "kw_to_w"),
    # mph -> m/s (1 mph = 0.44704 m/s)
    (re.compile(r"(?i)(_?mph)$"), "m_s", "mph_to_m_s"),
]


def _convert_values(series: pd.Series, mode: str) -> pd.Series:
    if not pd.api.types.is_numeric_dtype(series):
        return series
    
    if mode == "psi_to_bar":
        return series * 0.06894757293168361
    elif mode == "degf_to_degc":
        return (series - 32.0) * (5.0 / 9.0)
    elif mode == "kw_to_w":
        return series * 1000.0
    elif mode == "mph_to_m_s":
        return series * 0.44704
    return series


@register_plugin
class UnitStandardizerPlugin(BaseSchemaNormalizerPlugin):
    plugin_id = "unit_standardizer"
    plugin_name = "Unit Standardizer Normalizer Plugin"
    version = "1.0.0"
    stage = "normalizer"
    priority = 12

    def probe(self, context: PipelineContext) -> MatchResult:
        tables = context.assembled_tables or context.harvested_tables or context.parsed_tables
        if not tables:
            return MatchResult(supported=False, confidence=0.0, reasons=["No tables available for unit standardization"])

        matched_cols = 0
        for df in tables.values():
            if not df.empty:
                for col in df.columns:
                    col_str = str(col)
                    for pattern, _, _ in UNIT_RULES:
                        if pattern.search(col_str):
                            matched_cols += 1
                            break

        if matched_cols > 0:
            return MatchResult(
                supported=True,
                confidence=0.95,
                reasons=[f"Detected {matched_cols} numeric columns with non-standard physical unit suffixes"],
                detected_family="unit_standardizer",
            )

        return MatchResult(
            supported=False,
            confidence=0.0,
            reasons=["No columns matching physical unit patterns (psi, degF, kW, mph) found"],
        )

    def normalize(self, df: pd.DataFrame, context: PipelineContext) -> pd.DataFrame:
        if df.empty:
            return df

        df_out = df.copy()
        new_cols: List[str] = []
        converted_count = 0

        for col in df_out.columns:
            col_str = str(col)
            matched = False
            for pattern, new_suffix, mode in UNIT_RULES:
                match = pattern.search(col_str)
                if match:
                    old_unit_str = match.group(1)
                    # Preserve leading underscore if present
                    sep = "_" if old_unit_str.startswith("_") else ("_" if not col_str.endswith("_") else "")
                    prefix = col_str[:match.start()]
                    new_col_name = f"{prefix}{sep}{new_suffix}" if prefix else new_suffix
                    
                    df_out[col] = _convert_values(df_out[col], mode)
                    new_cols.append(new_col_name)
                    matched = True
                    converted_count += 1
                    break
            if not matched:
                new_cols.append(col_str)

        df_out.columns = new_cols

        if converted_count > 0:
            context.audits.append({
                "plugin_id": self.plugin_id,
                "action": "unit_standardization",
                "columns_converted": converted_count,
            })

        return df_out
