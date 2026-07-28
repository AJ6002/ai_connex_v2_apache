"""
models.py - Shared Data Models for Compiler Pipeline
=====================================================
Contains SchemaMap and JoinAudit dataclasses used across compiler.py and handoff.py.
Previously these lived in schema_mapper.py and relational_joiner.py (now deleted).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SchemaMap:
    """Bi-directional column name mapping and timestamp format metadata."""
    raw_to_canonical: Dict[str, str] = field(default_factory=dict)
    canonical_to_raw: Dict[str, str] = field(default_factory=dict)
    detected_timestamp_formats: Dict[str, str] = field(default_factory=dict)
    canonical_timestamp_col: Optional[str] = None
    canonical_group_col: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_to_canonical": self.raw_to_canonical,
            "canonical_to_raw": self.canonical_to_raw,
            "detected_timestamp_formats": self.detected_timestamp_formats,
            "canonical_timestamp_col": self.canonical_timestamp_col,
            "canonical_group_col": self.canonical_group_col,
            "warnings": self.warnings,
        }


@dataclass
class JoinAudit:
    """Audit record for a single table join operation."""
    group_id: str
    fact_file: str
    dimension_files: List[str]
    join_keys: List[str]
    join_type: str
    fact_rows_before: int
    merged_rows_after: int
    null_column_percentages: Dict[str, float]
    cartesian_guard_passed: bool
    warnings: List[str] = field(default_factory=list)
    redundant_keys_excluded: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "fact_file": self.fact_file,
            "dimension_files": self.dimension_files,
            "join_keys": self.join_keys,
            "join_type": self.join_type,
            "fact_rows_before": self.fact_rows_before,
            "merged_rows_after": self.merged_rows_after,
            "null_column_percentages": self.null_column_percentages,
            "cartesian_guard_passed": self.cartesian_guard_passed,
            "warnings": self.warnings,
            "redundant_keys_excluded": self.redundant_keys_excluded,
        }


def create_compiler_temp_dir(prefix: str = "aic_compiler_") -> Path:
    """Create a temporary working directory for the compiler, preferring workspace drive (X: drive) if available."""
    import os
    import tempfile
    from pathlib import Path

    ws_temp = Path(r"x:\TAS\AICONNEX\scratch\temp")
    try:
        ws_temp.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix=prefix, dir=ws_temp))
    except Exception:
        pass

    return Path(tempfile.mkdtemp(prefix=prefix))
