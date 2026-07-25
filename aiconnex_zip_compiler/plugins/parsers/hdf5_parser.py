"""
plugins/parsers/hdf5_parser.py - HDF5 Telemetry Parser Plugin
==============================================================
Stage 2 Parser plugin that extracts dataset matrices from HDF5 (.h5, .hdf5) archives.
Refactored from monolithic hdf5_converter.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin


@register_plugin
class Hdf5ParserPlugin(BaseParserPlugin):
    plugin_id = "hdf5_parser"
    plugin_name = "HDF5 Telemetry Parser Plugin"
    version = "1.0.0"
    priority = 70

    def probe(self, context: PipelineContext) -> MatchResult:
        h5_files = [item for item in context.inventory if item.format_ext in [".h5", ".hdf5"]]
        if h5_files:
            return MatchResult(
                supported=True,
                confidence=0.98,
                reasons=[f"Found {len(h5_files)} HDF5 telemetry file(s)"],
                detected_family="hdf5",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No HDF5 files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        try:
            import h5py

            def visitor(name, obj):
                if isinstance(obj, h5py.Dataset):
                    data = obj[()]
                    if len(data.shape) == 1:
                        df = pd.DataFrame({name.split("/")[-1]: data})
                    elif len(data.shape) == 2:
                        cols = [f"{name.split('/')[-1]}_{i}" for i in range(data.shape[1])]
                        df = pd.DataFrame(data, columns=cols)
                    else:
                        return
                    tbl_key = f"{filepath.stem}_{name.replace('/', '_')}"
                    results[tbl_key] = df

            with h5py.File(filepath, "r") as h5f:
                h5f.visititems(visitor)
        except ImportError:
            print("[Hdf5ParserPlugin] h5py not installed; skipping HDF5 parsing.")
        except Exception as e:
            print(f"[Hdf5ParserPlugin] Error parsing HDF5 {filepath}: {e}")

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext in [".h5", ".hdf5"]:
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
