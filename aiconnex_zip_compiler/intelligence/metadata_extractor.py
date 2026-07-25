"""
intelligence/metadata_extractor.py - Stage 4: Metadata Extraction
=================================================================
Computes real per-column statistics from parsed DataFrames. Fully
deterministic - no LLM, no domain assumptions, no name-based inference.

This is the evidence base that Stages 5 (schema roles), 6 (semantics), and
7 (problem discovery) reason over. The quality of the LLM's conclusions is
bounded by the quality of these statistics, so this stage computes:

  - dtype inference from actual values (not declared dtype)
  - missing percentage, unique count, cardinality ratio
  - constancy and monotonicity (key signals for id/time/counter columns)
  - min/max/mean/std for numerics
  - representative sample values
  - sampling interval estimate from datetime deltas
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .models import ColumnProfile, TableMetadata

logger = logging.getLogger(__name__)

MAX_SAMPLE_VALUES = 5
PROFILE_ROW_CAP = 50000  # stats computed on at most this many rows for speed


class MetadataExtractor:
    """Computes statistical profiles for parsed tables."""

    def extract_all(
        self,
        tables: Dict[str, pd.DataFrame],
        source_paths: Optional[Dict[str, str]] = None,
    ) -> List[TableMetadata]:
        """Profile every table in the dict."""
        source_paths = source_paths or {}
        results: List[TableMetadata] = []

        for table_name, df in tables.items():
            try:
                results.append(
                    self.extract_table(
                        table_name=table_name,
                        df=df,
                        source_path=source_paths.get(table_name, ""),
                    )
                )
            except Exception as e:
                logger.warning(f"[MetadataExtractor] Failed to profile '{table_name}': {e}")

        return results

    def extract_table(self, table_name: str, df: pd.DataFrame, source_path: str = "") -> TableMetadata:
        """Profile a single table."""
        if df is None or df.empty:
            return TableMetadata(
                table_name=table_name,
                source_path=source_path,
                row_count=0,
                column_count=0 if df is None else len(df.columns),
            )

        total_rows = len(df)
        sample_df = df.head(PROFILE_ROW_CAP) if total_rows > PROFILE_ROW_CAP else df

        columns: List[ColumnProfile] = []
        for position, col_name in enumerate(sample_df.columns):
            try:
                columns.append(self._profile_column(sample_df[col_name], str(col_name), position))
            except Exception as e:
                logger.debug(f"[MetadataExtractor] Column '{col_name}' profile failed: {e}")
                columns.append(
                    ColumnProfile(name=str(col_name), position=position, inferred_dtype="unknown")
                )

        try:
            duplicate_count = int(sample_df.duplicated().sum())
        except Exception:
            duplicate_count = 0

        return TableMetadata(
            table_name=table_name,
            source_path=source_path,
            row_count=total_rows,
            column_count=len(sample_df.columns),
            columns=columns,
            sampling_interval_guess=self._estimate_sampling_interval(sample_df, columns),
            duplicate_row_count=duplicate_count,
        )

    # -- Column profiling ---------------------------------------------------

    @staticmethod
    def _to_datetime_quiet(values: Any) -> pd.Series:
        """
        Parse to datetime without emitting pandas format-inference warnings.

        Statistical profiling deliberately probes columns that may not be dates,
        so the warnings are expected noise rather than actionable signal.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return pd.to_datetime(values, errors="coerce")

    def _profile_column(self, series: pd.Series, name: str, position: int) -> ColumnProfile:
        non_null = series.dropna()
        total = len(series)
        non_null_count = len(non_null)
        null_count = total - non_null_count

        profile = ColumnProfile(
            name=name,
            position=position,
            inferred_dtype="empty",
            non_null_count=non_null_count,
            null_count=null_count,
            missing_pct=round((null_count / total * 100) if total else 0.0, 2),
        )

        if non_null_count == 0:
            return profile

        try:
            unique_count = int(non_null.nunique())
        except Exception:
            unique_count = 0

        profile.unique_count = unique_count
        profile.cardinality_ratio = round(unique_count / non_null_count, 4) if non_null_count else 0.0
        profile.is_constant = unique_count == 1
        profile.inferred_dtype = self._infer_dtype(non_null)
        profile.sample_values = [self._stringify(v) for v in non_null.head(MAX_SAMPLE_VALUES).tolist()]

        if profile.inferred_dtype in ("numeric_int", "numeric_float"):
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if not numeric.empty:
                profile.min_value = self._stringify(numeric.min())
                profile.max_value = self._stringify(numeric.max())
                profile.mean_value = float(round(numeric.mean(), 6))
                profile.std_value = float(round(numeric.std(), 6)) if len(numeric) > 1 else 0.0
                try:
                    profile.is_monotonic_increasing = bool(numeric.is_monotonic_increasing)
                except Exception:
                    profile.is_monotonic_increasing = False

        elif profile.inferred_dtype == "datetime":
            parsed = self._to_datetime_quiet(non_null).dropna()
            if not parsed.empty:
                profile.min_value = self._stringify(parsed.min())
                profile.max_value = self._stringify(parsed.max())
                try:
                    profile.is_monotonic_increasing = bool(parsed.is_monotonic_increasing)
                except Exception:
                    profile.is_monotonic_increasing = False

        else:
            try:
                as_str = non_null.astype(str)
                profile.min_value = self._stringify(as_str.min())
                profile.max_value = self._stringify(as_str.max())
            except Exception:
                pass

        return profile

    @staticmethod
    def _infer_dtype(non_null: pd.Series) -> str:
        """Infer dtype from actual values rather than the declared pandas dtype."""
        if pd.api.types.is_bool_dtype(non_null):
            return "boolean"

        if pd.api.types.is_datetime64_any_dtype(non_null):
            return "datetime"

        if pd.api.types.is_integer_dtype(non_null):
            return "numeric_int"

        if pd.api.types.is_float_dtype(non_null):
            return "numeric_float"

        # Object dtype - probe what it actually contains
        sample = non_null.head(1000)

        numeric_parsed = pd.to_numeric(sample, errors="coerce")
        numeric_ratio = numeric_parsed.notna().sum() / max(1, len(sample))
        if numeric_ratio > 0.95:
            all_integral = bool(
                numeric_parsed.dropna().apply(lambda v: float(v).is_integer()).all()
            )
            return "numeric_int" if all_integral else "numeric_float"

        # Only attempt datetime parsing on non-numeric-looking data
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                datetime_parsed = pd.to_datetime(sample, errors="coerce")
            if datetime_parsed.notna().sum() / max(1, len(sample)) > 0.8:
                return "datetime"
        except Exception:
            pass

        unique_ratio = sample.nunique() / max(1, len(sample))
        return "categorical" if unique_ratio < 0.5 else "text"

    @staticmethod
    def _estimate_sampling_interval(
        df: pd.DataFrame, columns: List[ColumnProfile]
    ) -> Optional[str]:
        """
        Estimate the time step from the first monotonic datetime column.
        Structural only - reports the observed median delta, no interpretation.
        """
        datetime_cols = [
            c.name for c in columns if c.inferred_dtype == "datetime" and c.is_monotonic_increasing
        ]
        if not datetime_cols:
            datetime_cols = [c.name for c in columns if c.inferred_dtype == "datetime"]

        for col_name in datetime_cols:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    parsed = pd.to_datetime(df[col_name], errors="coerce").dropna()
                if len(parsed) < 3:
                    continue
                deltas = parsed.sort_values().diff().dropna()
                if deltas.empty:
                    continue
                median_delta = deltas.median()
                if pd.isna(median_delta):
                    continue
                return str(median_delta)
            except Exception:
                continue

        return None

    @staticmethod
    def _stringify(value: Any) -> str:
        """Compact, JSON-safe string form of a cell value."""
        try:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return ""
            if isinstance(value, (np.integer,)):
                return str(int(value))
            if isinstance(value, (np.floating,)):
                return f"{float(value):.6g}"
            text = str(value)
            return text if len(text) <= 80 else text[:77] + "..."
        except Exception:
            return ""
