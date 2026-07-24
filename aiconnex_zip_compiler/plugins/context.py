"""
plugins/context.py — Shared State, Execution Context, Plugin Snapshot & Lockfile
=================================================================================
Carries mutable dataset context between pipeline stages, captures immutable
run snapshots, and generates reproducible `compiler_lock.json` lockfiles.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class FileInventoryItem:
    filepath: Path
    relative_path: str
    size_bytes: int
    format_ext: str
    detected_role: str = "unknown"  # "fact" | "dimension" | "snapshot" | "metadata"


@dataclass
class PipelineContext:
    """Carries dataset execution state across the 5 compiler pipeline stages."""
    target_path: Path
    temp_dir: Path
    output_dir: Path
    
    # Policy overrides from dataset manifest or user configuration
    policy_overrides: Dict[str, str] = field(default_factory=dict)  # stage -> plugin_id
    
    # Stage outputs
    inventory: List[FileInventoryItem] = field(default_factory=list)
    layout_type: str = "unknown"  # "zip_directory" | "snapshot_folder" | "single_file"
    join_keys: List[str] = field(default_factory=list)
    primary_timestamp_col: Optional[str] = None
    
    # Parsed DataFrames keyed by table/file name
    parsed_tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    
    # Assembled DataFrames after stage 3
    assembled_tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    
    # Harvested feature DataFrames after stage 4
    harvested_tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    
    # Normalized canonical DataFrames after stage 5
    normalized_tables: Dict[str, pd.DataFrame] = field(default_factory=dict)
    
    # Lockfile & execution metadata
    active_plugins: Dict[str, str] = field(default_factory=dict)  # plugin_id -> version
    audits: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedPlugin:
    plugin_id: str
    version: str
    contract_version: int
    stage: str
    priority: int


@dataclass(frozen=True)
class PluginSnapshot:
    """Immutable snapshot of all resolved plugin versions for a single compiler run."""
    compiler_version: str
    run_timestamp: str
    resolved_plugins: Dict[str, ResolvedPlugin]  # stage -> ResolvedPlugin

    def to_lockfile_dict(self) -> Dict[str, Any]:
        return {
            "compiler_version": self.compiler_version,
            "run_timestamp": self.run_timestamp,
            "plugin_lock": {
                stage: {
                    "plugin_id": p.plugin_id,
                    "version": p.version,
                    "contract_version": p.contract_version,
                    "priority": p.priority,
                }
                for stage, p in self.resolved_plugins.items()
            },
        }

    def write_lockfile(self, destination: Path) -> Path:
        lockfile_path = destination / "compiler_lock.json"
        lockfile_path.write_text(json.dumps(self.to_lockfile_dict(), indent=2), encoding="utf-8")
        return lockfile_path
