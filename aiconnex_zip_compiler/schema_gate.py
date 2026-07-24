"""
schema_gate.py — Lightweight Entry Schema Gate & Ingestion Router
===================================================================
Pre-compilation gate that validates incoming raw archives before heavy compilation:
1. Validates archive integrity (non-empty, valid ZIP/file format, non-corrupt).
2. Inspects file extensions & structure to route to appropriate converter hooks.
3. Gates invalid or un-parseable inputs early with clear actionable diagnostic status.
"""

from __future__ import annotations

import logging
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


@dataclass
class SchemaGateDecision:
    is_valid: bool
    detected_formats: List[str]
    primary_route: str
    file_count: int
    total_size_bytes: int
    gate_message: str


class SchemaGate:
    """
    Lightweight Entry Schema Gate & Ingestion Router.
    Inspects incoming archive files before running full discovery and schema mapping.
    """

    SUPPORTED_EXTENSIONS = {".csv", ".txt", ".xlsx", ".xls", ".mat", ".h5", ".hdf5", ".zip", ".parquet", ".json"}

    def __init__(self, target_path: Path):
        self.target_path = Path(target_path)

    def evaluate(self) -> SchemaGateDecision:
        """
        Evaluates incoming path, inspects format/structure, and decides routing path.
        """
        if not self.target_path.exists():
            return SchemaGateDecision(
                is_valid=False,
                detected_formats=[],
                primary_route="invalid_path",
                file_count=0,
                total_size_bytes=0,
                gate_message=f"File path does not exist: {self.target_path}",
            )

        # Single CSV/Excel file ingestion
        if self.target_path.is_file() and self.target_path.suffix.lower() != ".zip":
            ext = self.target_path.suffix.lower()
            return SchemaGateDecision(
                is_valid=ext in self.SUPPORTED_EXTENSIONS,
                detected_formats=[ext],
                primary_route=f"direct_{ext.strip('.')}",
                file_count=1,
                total_size_bytes=self.target_path.stat().st_size,
                gate_message=f"Direct file ingestion for format {ext}",
            )

        # ZIP archive ingestion
        if self.target_path.is_file() and self.target_path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(self.target_path, "r") as zf:
                    namelist = zf.namelist()
                    if not namelist:
                        return SchemaGateDecision(
                            is_valid=False,
                            detected_formats=[],
                            primary_route="empty_archive",
                            file_count=0,
                            total_size_bytes=0,
                            gate_message="Archive is empty",
                        )

                    formats = set()
                    for name in namelist:
                        ext = Path(name).suffix.lower()
                        if ext:
                            formats.add(ext)

                    # Determine primary converter route
                    primary_route = "flat_csv"
                    if ".xlsx" in formats or ".xls" in formats:
                        primary_route = "scada_excel"
                    elif ".h5" in formats or ".hdf5" in formats:
                        primary_route = "hdf5_telemetry"
                    elif ".mat" in formats:
                        primary_route = "matlab_struct"
                    elif ".zip" in formats:
                        primary_route = "nested_zip"

                    return SchemaGateDecision(
                        is_valid=True,
                        detected_formats=list(formats),
                        primary_route=primary_route,
                        file_count=len(namelist),
                        total_size_bytes=self.target_path.stat().st_size,
                        gate_message=f"Archive validated ({len(namelist)} files, formats: {list(formats)})",
                    )
            except zipfile.BadZipFile:
                return SchemaGateDecision(
                    is_valid=False,
                    detected_formats=[],
                    primary_route="corrupt_zip",
                    file_count=0,
                    total_size_bytes=0,
                    gate_message="Corrupt or invalid ZIP archive",
                )

        # Directory ingestion
        if self.target_path.is_dir():
            files = [p for p in self.target_path.rglob("*") if p.is_file()]
            formats = list(set(p.suffix.lower() for p in files if p.suffix))
            return SchemaGateDecision(
                is_valid=len(files) > 0,
                detected_formats=formats,
                primary_route="directory_scan",
                file_count=len(files),
                total_size_bytes=sum(p.stat().st_size for p in files),
                gate_message=f"Directory validated ({len(files)} files)",
            )

        return SchemaGateDecision(
            is_valid=False,
            detected_formats=[],
            primary_route="unknown",
            file_count=0,
            total_size_bytes=0,
            gate_message="Unsupported input type",
        )
