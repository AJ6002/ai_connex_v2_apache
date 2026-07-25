"""
reporter.py - Structured Compilation Failure Reporter & Gap Classifier
======================================================================
Captures structured failure metadata when a dataset compilation fails,
classifies the failure into known Gap IDs (G-01 through G-12), and emits
input context for the Scout Agent loop.
"""

from __future__ import annotations

import os
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ArchiveNode:
    filename: str
    relative_path: str
    size_bytes: int
    format: str  # "csv" | "txt" | "mat" | "h5" | "xlsx" | "zip" | "unknown"


@dataclass
class CompilationFailureReport:
    zip_path: str
    zip_stem: str
    error_message: str
    traceback_str: str
    failing_module: str
    failing_line: int
    gap_id: str  # e.g. "G-01", "G-03", "G-05", "G-09", "G-99" (Unknown)
    gap_description: str
    target_stage: str = "parser"  # "discovery" | "parser" | "assembler" | "harvester" | "normalizer"
    target_plugin_interface: str = "BaseParserPlugin"  # The ABC the new plugin must implement
    contract_version: int = 1  # Plugin API contract version expected
    archive_tree: List[ArchiveNode] = field(default_factory=list)
    suggested_fix_type: str = "new_plugin"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zip_path": self.zip_path,
            "zip_stem": self.zip_stem,
            "error_message": self.error_message,
            "traceback_str": self.traceback_str,
            "failing_module": self.failing_module,
            "failing_line": self.failing_line,
            "gap_id": self.gap_id,
            "gap_description": self.gap_description,
            "target_stage": self.target_stage,
            "target_plugin_interface": self.target_plugin_interface,
            "contract_version": self.contract_version,
            "archive_tree": [
                {
                    "filename": node.filename,
                    "relative_path": node.relative_path,
                    "size_bytes": node.size_bytes,
                    "format": node.format,
                }
                for node in self.archive_tree
            ],
            "suggested_fix_type": self.suggested_fix_type,
        }


KNOWN_GAP_PATTERNS = [
    # (gap_id, keywords, description, target_stage, target_plugin_interface)
    ("G-01", ["hdf5", ".h5", "h5py", "HDF5"], "HDF5 / .h5 file format not supported", "parser", "BaseParserPlugin"),
    ("G-02", ["parquet", ".parquet", "arrow", "pyarrow"], "Parquet / Arrow file format not supported", "parser", "BaseParserPlugin"),
    ("G-03", ["mat", "matlab", "scipy.io", "KeyError: 'cycle'"], "Non-standard MATLAB struct shape", "parser", "BaseParserPlugin"),
    ("G-04", ["tdms", "nptdms", "LabVIEW"], "TDMS measurement format not supported", "parser", "BaseParserPlugin"),
    ("G-05", ["excel", "xlsx", "xls", "openpyxl"], "Excel multi-sheet / non-standard header format", "parser", "BaseParserPlugin"),
    ("G-06", ["target", "rul", "label", "missing target"], "Automatic target / RUL synthesis failure", "assembler", "BaseAssemblerPlugin"),
    ("G-07", ["entity", "alignment", "cross-archive", "train.*test"], "Cross-archive entity resolution", "assembler", "BaseAssemblerPlugin"),
    ("G-08", ["resample", "sampling rate", "frequency", "20kHz"], "Sampling rate normalization", "harvester", "BaseFeatureHarvesterPlugin"),
    ("G-09", ["nested", "recursion", "depth", "deep"], "Deeply nested folder hierarchy (>3 levels)", "discovery", "BaseDiscoveryPlugin"),
    ("G-10", ["trainability", "No CSV", "empty", "no files"], "No parseable files found / discovery failure", "discovery", "BaseDiscoveryPlugin"),
    ("G-11", ["image", "binary", "thermal", "waveform plot"], "Binary/image data not supported", "parser", "BaseParserPlugin"),
    ("G-12", ["readme", "metadata", "contextual", "pdf"], "Contextual metadata parsing", "normalizer", "BaseSchemaNormalizerPlugin"),
]


def classify_compilation_failure(
    zip_path: Path,
    temp_dir: Optional[Path],
    exception: Exception,
) -> CompilationFailureReport:
    """
    Analyzes an exception during dataset compilation and builds a structured failure report.
    """
    tb_str = traceback.format_exc()
    exc_type, exc_val, exc_tb = sys.exc_info()

    failing_module = "unknown"
    failing_line = 0
    if exc_tb:
        last_frame = traceback.extract_tb(exc_tb)[-1]
        failing_module = f"{Path(last_frame.filename).name}:{last_frame.name}"
        failing_line = last_frame.lineno

    err_msg = str(exception)
    full_text = f"{err_msg} {tb_str}"

    # Classify Gap ID
    gap_id = "G-99"
    gap_desc = "Unclassified archive compilation failure"
    fix_type = "new_plugin"
    target_stage = "parser"
    target_interface = "BaseParserPlugin"

    for gid, keywords, desc, stage, interface in KNOWN_GAP_PATTERNS:
        if any(kw.lower() in full_text.lower() for kw in keywords):
            gap_id = gid
            gap_desc = desc
            target_stage = stage
            target_interface = interface
            break

    # Build archive file tree
    tree_nodes: List[ArchiveNode] = []
    if temp_dir and temp_dir.exists():
        for root, _, files in os.walk(temp_dir):
            for f in files:
                fpath = Path(root) / f
                rel_path = str(fpath.relative_to(temp_dir))
                fmt = fpath.suffix.lower().lstrip(".") or "unknown"
                tree_nodes.append(
                    ArchiveNode(
                        filename=f,
                        relative_path=rel_path,
                        size_bytes=fpath.stat().st_size if fpath.exists() else 0,
                        format=fmt,
                    )
                )

    return CompilationFailureReport(
        zip_path=str(zip_path),
        zip_stem=zip_path.stem,
        error_message=err_msg,
        traceback_str=tb_str,
        failing_module=failing_module,
        failing_line=failing_line,
        gap_id=gap_id,
        gap_description=gap_desc,
        target_stage=target_stage,
        target_plugin_interface=target_interface,
        contract_version=1,
        archive_tree=tree_nodes,
        suggested_fix_type=fix_type,
    )
