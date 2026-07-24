"""
plugins/discovery/zip_directory_discovery.py — General Zip & Directory Discovery Plugin
========================================================================================
Stage 1 Discovery plugin that walks ZIP archives or directories, extracts files to temp,
recursively unpacks nested ZIP archives, and populates PipelineContext inventory.
"""

from __future__ import annotations

import logging
import os
import zipfile
from pathlib import Path
from typing import List

from ..base import BaseDiscoveryPlugin, MatchResult
from ..context import PipelineContext, FileInventoryItem
from ..registry import register_plugin

logger = logging.getLogger(__name__)


def _unpack_nested_zips(directory: Path, max_depth: int = 5, _current_depth: int = 0) -> None:
    """Recursively unpack any nested .zip files found inside the extracted directory."""
    if _current_depth >= max_depth:
        logger.warning(f"[ZipDiscovery] Max nested ZIP depth ({max_depth}) reached at {directory}")
        return

    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(".zip"):
                zip_path = Path(root) / f
                extract_target = zip_path.with_suffix("")
                try:
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(extract_target)
                    logger.debug(f"[ZipDiscovery] Unpacked nested ZIP: {zip_path.name} → {extract_target}")
                    # Recurse into extracted contents
                    _unpack_nested_zips(extract_target, max_depth, _current_depth + 1)
                except (zipfile.BadZipFile, Exception) as e:
                    logger.warning(f"[ZipDiscovery] Failed to unpack nested ZIP {zip_path.name}: {e}")


@register_plugin
class ZipDirectoryDiscoveryPlugin(BaseDiscoveryPlugin):
    plugin_id = "zip_directory_discovery"
    plugin_name = "ZIP & Directory Discovery Plugin"
    version = "1.1.0"
    priority = 10  # Standard priority for general directory/zip walking

    def probe(self, context: PipelineContext) -> MatchResult:
        p = context.target_path
        if p.exists() and (p.is_dir() or p.suffix.lower() in [".zip", ".tar", ".gz"]):
            return MatchResult(
                supported=True,
                confidence=0.90,
                reasons=[f"Valid path exists and is container ({p.suffix or 'directory'})"],
                detected_family="zip_directory",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["Path does not exist or is unsupported single binary"])

    def discover(self, target_path: Path, context: PipelineContext) -> PipelineContext:
        extracted_dir = context.temp_dir / "raw_extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        if target_path.is_file() and target_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(target_path, "r") as zf:
                zf.extractall(extracted_dir)
            # Recursively unpack nested ZIP archives
            _unpack_nested_zips(extracted_dir)
            base_scan = extracted_dir
        elif target_path.is_dir():
            base_scan = target_path
        else:
            base_scan = target_path.parent

        # Exclude non-data files (READMEs, licenses, nested .zip files already extracted)
        exclude_prefixes = ("readme", "license", "changelog", "about", "__macosx", ".ds_store")

        inventory: List[FileInventoryItem] = []
        for p in base_scan.rglob("*"):
            if p.is_file():
                # Skip already-extracted zip files and non-data docs
                if p.suffix.lower() == ".zip":
                    continue
                if p.name.lower().startswith(exclude_prefixes):
                    continue

                ext = p.suffix.lower()
                rel_path = str(p.relative_to(base_scan))
                item = FileInventoryItem(
                    filepath=p,
                    relative_path=rel_path,
                    size_bytes=p.stat().st_size,
                    format_ext=ext,
                )
                inventory.append(item)

        context.inventory = inventory
        context.layout_type = "zip_directory"
        logger.info(f"[ZipDiscovery] Discovered {len(inventory)} files from '{target_path.name}'")
        return context
