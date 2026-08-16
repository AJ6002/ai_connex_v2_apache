"""
plugins/discovery/archive_manifest_discovery.py - Archive Manifest Catalog Discovery Plugin
=============================================================================================
Stage 1 Discovery plugin that scans archive inventories, catalogs all files, formats,
sizes, and inner directory structures.
"""

from __future__ import annotations

import os
import zipfile
import logging
from pathlib import Path
from typing import List, Set

from ..base import BaseDiscoveryPlugin, MatchResult
from ..context import PipelineContext, FileInventoryItem
from ..registry import register_plugin

logger = logging.getLogger(__name__)


def _unpack_nested_zips(directory: Path, max_depth: int = 5, _current_depth: int = 0) -> None:
    """Recursively unpack nested ZIP files within target directory."""
    if _current_depth >= max_depth:
        return
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(".zip"):
                zip_path = Path(root) / f
                extract_target = zip_path.with_suffix("")
                try:
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(extract_target)
                    _unpack_nested_zips(extract_target, max_depth, _current_depth + 1)
                except Exception as e:
                    logger.warning(f"[ArchiveManifestDiscovery] Failed unpacking nested zip {zip_path}: {e}")


@register_plugin
class ArchiveManifestDiscoveryPlugin(BaseDiscoveryPlugin):
    plugin_id = "archive_manifest_discovery"
    plugin_name = "Archive Manifest Discovery Plugin"
    version = "1.0.0"
    stage = "discovery"
    priority = 5

    def probe(self, context: PipelineContext) -> MatchResult:
        p = context.target_path
        if context.inventory or (p and p.exists()):
            return MatchResult(
                supported=True,
                confidence=0.85,
                reasons=[f"Target path '{p.name if p else 'N/A'}' or inventory available for manifest cataloging"],
                detected_family="archive_manifest",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["Target path does not exist"])

    def discover(self, target_path: Path, context: PipelineContext) -> PipelineContext:
        extracted_dir = context.temp_dir / "raw_extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        if target_path.is_file() and target_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(target_path, "r") as zf:
                zf.extractall(extracted_dir)
            _unpack_nested_zips(extracted_dir)
            base_scan = extracted_dir
        elif target_path.is_dir():
            base_scan = target_path
        else:
            base_scan = target_path.parent

        exclude_prefixes = ("readme", "license", "changelog", "about", "__macosx", ".ds_store")

        inventory: List[FileInventoryItem] = []
        formats: Set[str] = set()
        inner_dirs: Set[str] = set()
        total_size = 0

        for p in base_scan.rglob("*"):
            if p.is_dir():
                rel_dir = str(p.relative_to(base_scan))
                if rel_dir and rel_dir != ".":
                    dir_part = Path(rel_dir).parts[0]
                    inner_dirs.add(dir_part)
            elif p.is_file():
                if p.suffix.lower() == ".zip" or p.name.lower().startswith(exclude_prefixes):
                    continue
                ext = p.suffix.lower() or ".unknown"
                rel_path = str(p.relative_to(base_scan))
                size = p.stat().st_size

                formats.add(ext)
                total_size += size

                item = FileInventoryItem(
                    filepath=p,
                    relative_path=rel_path,
                    size_bytes=size,
                    format_ext=ext,
                )
                inventory.append(item)

        context.inventory = inventory
        if not context.layout_type or context.layout_type == "unknown":
            context.layout_type = "archive_manifest"

        audit_entry = {
            "plugin_id": self.plugin_id,
            "stage": self.stage,
            "file_count": len(inventory),
            "total_size_bytes": total_size,
            "formats": sorted(list(formats)),
            "inner_directories": sorted(list(inner_dirs)),
            "catalog": [
                {
                    "relative_path": item.relative_path,
                    "format": item.format_ext,
                    "size_bytes": item.size_bytes,
                }
                for item in inventory
            ],
        }
        context.audits.append(audit_entry)
        logger.info(f"[ArchiveManifestDiscovery] Cataloged {len(inventory)} files across {len(inner_dirs)} directories")
        return context
