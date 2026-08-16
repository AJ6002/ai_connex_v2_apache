"""
plugins/discovery/snapshot_folder_discovery.py - Bearing / Signal Snapshot Discovery Plugin
=============================================================================================
Stage 1 Discovery plugin that detects directories with sequential vibration snapshot files
(e.g., FEMTO bearing dataset containing acc_XXXXX.csv files).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from ..base import BaseDiscoveryPlugin, MatchResult
from ..context import PipelineContext, FileInventoryItem
from ..registry import register_plugin


@register_plugin
class SnapshotFolderDiscoveryPlugin(BaseDiscoveryPlugin):
    plugin_id = "snapshot_folder_discovery"
    plugin_name = "Snapshot Folder Discovery Plugin"
    version = "1.0.0"
    priority = 80  # High priority to catch snapshot structures before generic directory scanner

    def probe(self, context: PipelineContext) -> MatchResult:
        p = context.target_path
        if not p.exists():
            return MatchResult(supported=False, confidence=0.0, reasons=["Path does not exist"])

        acc_count = 0
        if p.is_dir():
            for root, _, files in os.walk(p):
                acc_files = [f for f in files if f.lower().startswith("acc_") and f.lower().endswith(".csv")]
                acc_count += len(acc_files)
                if acc_count >= 10:
                    return MatchResult(
                        supported=True,
                        confidence=0.98,
                        reasons=[f"Detected {acc_count}+ bearing snapshot files (acc_*.csv)"],
                        detected_family="snapshot_folder",
                    )
        return MatchResult(supported=False, confidence=0.1, reasons=["No snapshot folder structure detected"])

    def discover(self, target_path: Path, context: PipelineContext) -> PipelineContext:
        inventory: List[FileInventoryItem] = []
        for p in target_path.rglob("*"):
            if p.is_file() and p.name.lower().startswith("acc_") and p.suffix.lower() == ".csv":
                rel_path = str(p.relative_to(target_path))
                inventory.append(
                    FileInventoryItem(
                        filepath=p,
                        relative_path=rel_path,
                        size_bytes=p.stat().st_size,
                        format_ext=".csv",
                        detected_role="snapshot",
                    )
                )

        context.inventory = inventory
        context.layout_type = "snapshot_folder"
        return context
