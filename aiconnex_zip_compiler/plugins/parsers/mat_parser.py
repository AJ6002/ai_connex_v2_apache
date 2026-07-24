"""
plugins/parsers/mat_parser.py — MATLAB .mat Struct Parser Plugin
==================================================================
Stage 2 Parser plugin for MATLAB .mat struct archives (e.g. NASA Li-ion battery aging datasets).
Extracts cycle-based voltage, current, temperature arrays and computes statistical summaries
per cycle for downstream ML training.

Refactored from monolithic mat_converter.py.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)


@register_plugin
class MatParserPlugin(BaseParserPlugin):
    plugin_id = "mat_parser"
    plugin_name = "MATLAB .mat Struct Parser Plugin"
    version = "1.1.0"
    priority = 70

    def probe(self, context: PipelineContext) -> MatchResult:
        mat_files = [item for item in context.inventory if item.format_ext == ".mat"]
        if mat_files:
            return MatchResult(
                supported=True,
                confidence=0.98,
                reasons=[f"Found {len(mat_files)} MATLAB .mat file(s)"],
                detected_family="matlab",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No .mat files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        try:
            import scipy.io

            mat = scipy.io.loadmat(str(filepath))
            keys = [k for k in mat.keys() if not k.startswith("__")]

            if not keys:
                return results

            records: List[Dict] = []

            for key in keys:
                obj = mat[key]

                # ── NASA Battery struct pattern (cycle-based with voltage/current/temp arrays) ──
                if hasattr(obj, "dtype") and obj.dtype.names and "cycle" in obj.dtype.names:
                    struct = obj[0, 0]
                    cycles = struct["cycle"][0]

                    discharge_idx = 0
                    for c_idx, cycle in enumerate(cycles):
                        c_type = str(cycle["type"][0]) if "type" in cycle.dtype.names else "unknown"

                        if "data" not in cycle.dtype.names:
                            continue

                        data = cycle["data"][0, 0]

                        # Extract measurement arrays
                        v_measured = (
                            data["Voltage_measured"][0].flatten()
                            if "Voltage_measured" in data.dtype.names and len(data["Voltage_measured"]) > 0
                            else np.array([])
                        )
                        i_measured = (
                            data["Current_measured"][0].flatten()
                            if "Current_measured" in data.dtype.names and len(data["Current_measured"]) > 0
                            else np.array([])
                        )
                        t_measured = (
                            data["Temperature_measured"][0].flatten()
                            if "Temperature_measured" in data.dtype.names and len(data["Temperature_measured"]) > 0
                            else np.array([])
                        )
                        time_seq = (
                            data["Time"][0].flatten()
                            if "Time" in data.dtype.names and len(data["Time"]) > 0
                            else np.array([])
                        )

                        # Capacity extraction
                        cap = np.nan
                        if "Capacity" in data.dtype.names and len(data["Capacity"]) > 0:
                            try:
                                cap = float(data["Capacity"][0][0])
                            except (IndexError, TypeError, ValueError):
                                cap = np.nan

                        if len(v_measured) > 0:
                            discharge_idx += 1
                            rec = {
                                "asset_id": filepath.stem,
                                "cycle_id": discharge_idx,
                                "type": c_type,
                                "capacity_ahr": cap,
                                "v_mean": float(np.mean(v_measured)),
                                "v_min": float(np.min(v_measured)),
                                "v_max": float(np.max(v_measured)),
                                "v_std": float(np.std(v_measured)),
                                "i_mean": float(np.mean(i_measured)) if len(i_measured) > 0 else 0.0,
                                "t_mean": float(np.mean(t_measured)) if len(t_measured) > 0 else 0.0,
                                "t_max": float(np.max(t_measured)) if len(t_measured) > 0 else 0.0,
                                "duration_sec": (
                                    float(time_seq[-1] - time_seq[0]) if len(time_seq) > 1 else 0.0
                                ),
                            }
                            records.append(rec)

            if records:
                df = pd.DataFrame(records)
                # Synthesize RUL countdown target from capacity degradation curve
                if "capacity_ahr" in df.columns:
                    df_valid = df.dropna(subset=["capacity_ahr"]).copy()
                    total_n = len(df_valid)
                    df_valid["RUL"] = [total_n - (i + 1) for i in range(total_n)]
                    df = df_valid

                results[f"{filepath.stem}_cycles"] = df
                logger.info(
                    f"[MatParser] Extracted {len(df)} cycles from '{filepath.name}' "
                    f"({len(df.columns)} features incl. RUL)"
                )

        except ImportError:
            logger.warning("[MatParserPlugin] scipy not installed; skipping .mat parsing.")
        except Exception as e:
            logger.warning(f"[MatParserPlugin] Error parsing {filepath}: {e}")

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext == ".mat":
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
