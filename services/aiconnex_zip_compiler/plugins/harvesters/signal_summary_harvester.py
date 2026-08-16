"""
plugins/harvesters/signal_summary_harvester.py - Signal & Snapshot Feature Harvester Plugin
=============================================================================================
Stage 4 Harvester plugin that computes 14 statistical time-domain and frequency-domain features
over raw high-frequency vibration/sensor snapshot CSV files (e.g. FEMTO / IMS bearing datasets).
Refactored from monolithic snapshot_aggregator.py.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd

from ..base import BaseFeatureHarvesterPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


@register_plugin
class SignalSummaryHarvesterPlugin(BaseFeatureHarvesterPlugin):
    plugin_id = "signal_summary_harvester"
    plugin_name = "Signal & Snapshot Feature Harvester Plugin"
    version = "1.0.0"
    priority = 80

    def probe(self, context: PipelineContext) -> MatchResult:
        if context.layout_type == "snapshot_folder":
            return MatchResult(
                supported=True,
                confidence=0.98,
                reasons=["Snapshot folder layout detected in context"],
                detected_family="signal_harvester",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["Not a snapshot folder layout"])

    def harvest(self, tables: Dict[str, pd.DataFrame], context: PipelineContext) -> Dict[str, pd.DataFrame]:
        input_tables = tables or getattr(context, "parsed_tables", {})
        snapshot_items = [item for item in context.inventory if item.detected_role == "snapshot"]

        feature_sources: List[pd.DataFrame | Path] = []

        if snapshot_items:
            for item in snapshot_items:
                # Check for in-memory table match first
                df = (
                    input_tables.get(item.relative_path)
                    or input_tables.get(item.filepath.name)
                    or input_tables.get(str(item.filepath))
                )
                if df is not None:
                    feature_sources.append(df)
                else:
                    feature_sources.append(item.filepath)
        elif input_tables:
            # If no inventory snapshot items present, consume provided in-memory tables
            feature_sources = list(input_tables.values())

        if not feature_sources:
            return {}

        feature_rows: List[Dict[str, float]] = []
        total_count = len(feature_sources)
        for idx, source in enumerate(feature_sources):
            stats = self._extract_snapshot_features(source)
            stats["snapshot_index"] = idx + 1
            stats["rul"] = float(total_count - idx - 1)  # Synthetic RUL target
            feature_rows.append(stats)

        harvested_df = pd.DataFrame(feature_rows)
        return {"bearing_snapshot_features": harvested_df}

    def _extract_snapshot_features(self, target: pd.DataFrame | Path | str) -> Dict[str, float]:
        try:
            if isinstance(target, pd.DataFrame):
                df = target
            else:
                df = pd.read_csv(target, header=None)

            if df.shape[1] >= 6:
                h_acc = df.iloc[:, 4].values
                v_acc = df.iloc[:, 5].values
            elif df.shape[1] >= 2:
                h_acc = df.iloc[:, -2].values
                v_acc = df.iloc[:, -1].values
            else:
                h_acc = df.iloc[:, 0].values
                v_acc = df.iloc[:, 0].values

            def calc_stats(arr: np.ndarray, prefix: str) -> Dict[str, float]:
                arr_clean = np.nan_to_num(arr, nan=0.0)
                mean_val = float(np.mean(arr_clean))
                std_val = float(np.std(arr_clean))
                rms_val = float(np.sqrt(np.mean(arr_clean**2)))
                peak_val = float(np.max(np.abs(arr_clean)))

                n = len(arr_clean)
                kurtosis_val = float(np.sum((arr_clean - mean_val)**4) / (n * (std_val**4 + 1e-9))) if std_val > 0 else 0.0
                skewness_val = float(np.sum((arr_clean - mean_val)**3) / (n * (std_val**3 + 1e-9))) if std_val > 0 else 0.0
                crest_factor = peak_val / (rms_val + 1e-9)

                return {
                    f"{prefix}_mean": mean_val,
                    f"{prefix}_std": std_val,
                    f"{prefix}_rms": rms_val,
                    f"{prefix}_peak": peak_val,
                    f"{prefix}_kurtosis": kurtosis_val,
                    f"{prefix}_skewness": skewness_val,
                    f"{prefix}_crest_factor": crest_factor,
                }

            out = {}
            out.update(calc_stats(h_acc, "acc_horiz"))
            out.update(calc_stats(v_acc, "acc_vert"))
            return out
        except Exception:
            return {}

