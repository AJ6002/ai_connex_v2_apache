"""
schema_mapper.py — Layer 2: Schema Mapping & Timestamp Normalization
=====================================================================
Standardizes timestamp columns into unified datetime objects across all files,
builds bi-directional raw <-> canonical column name mappings, and exports
schema lineage metadata (zero value modification or scaling).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd


@dataclass
class SchemaMap:
    raw_to_canonical: Dict[str, str] = field(default_factory=dict)
    canonical_to_raw: Dict[str, str] = field(default_factory=dict)
    detected_timestamp_formats: Dict[str, str] = field(default_factory=dict)
    canonical_timestamp_col: Optional[str] = None
    canonical_group_col: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_to_canonical": self.raw_to_canonical,
            "canonical_to_raw": self.canonical_to_raw,
            "detected_timestamp_formats": self.detected_timestamp_formats,
            "canonical_timestamp_col": self.canonical_timestamp_col,
            "canonical_group_col": self.canonical_group_col,
        }


def to_snake_case(name: str) -> str:
    """Convert raw column header to clean canonical snake_case name."""
    s = name.strip()
    s = re.sub(r"[\s\-\/\.]+", "_", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = re.sub(r"[^\w_]", "", s)
    return s.lower().strip("_")


def normalize_schema_and_timestamps(
    df: pd.DataFrame,
    filename: str,
    raw_ts_col: Optional[str],
    raw_group_col: Optional[str],
    schema_map: SchemaMap,
) -> pd.DataFrame:
    """
    Parse timestamps into normalized pd.Timestamp and map column names
    to canonical lowercase snake_case. Modifies schema_map lineage in-place.
    """
    df_out = df.copy()

    # 1. Column Naming Canonicalization & Mapping
    col_mapping = {}
    for col in df_out.columns:
        canonical = to_snake_case(col)
        # Avoid duplicate column collisions
        if canonical in col_mapping.values():
            canonical = f"{canonical}_{filename.split('.')[0].lower()}"

        col_mapping[col] = canonical
        schema_map.raw_to_canonical[col] = canonical
        schema_map.canonical_to_raw[canonical] = col

    df_out = df_out.rename(columns=col_mapping)

    # 2. Timestamp Parsing & Normalization
    if raw_ts_col and (raw_ts_col in df.columns or to_snake_case(raw_ts_col) in df_out.columns):
        canonical_ts = col_mapping.get(raw_ts_col, to_snake_case(raw_ts_col))
        schema_map.canonical_timestamp_col = canonical_ts

        # Detect format
        ts_series = df[raw_ts_col] if raw_ts_col in df.columns else (df_out[canonical_ts] if canonical_ts in df_out.columns else None)
        sample_str = str(ts_series.dropna().iloc[0]) if ts_series is not None and not ts_series.dropna().empty else ""
        detected_fmt = "ISO8601 / Inferred"

        if canonical_ts in df_out.columns:
            try:
                # Parse with dayfirst=True fallback for DD-MM-YYYY format
                df_out[canonical_ts] = pd.to_datetime(df_out[canonical_ts], dayfirst=True, errors="coerce")
                if "-" in sample_str and sample_str.find("-") == 2:
                    detected_fmt = "DD-MM-YYYY HH:MM:SS"
                elif "-" in sample_str and sample_str.find("-") == 4:
                    detected_fmt = "YYYY-MM-DD HH:MM:SS"
            except Exception:
                df_out[canonical_ts] = pd.to_datetime(df_out[canonical_ts], errors="coerce")

        schema_map.detected_timestamp_formats[filename] = detected_fmt

    # Record group col
    if raw_group_col and raw_group_col in df.columns:
        schema_map.canonical_group_col = col_mapping.get(raw_group_col, to_snake_case(raw_group_col))

    return df_out
