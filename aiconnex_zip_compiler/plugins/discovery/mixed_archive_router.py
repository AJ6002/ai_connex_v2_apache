"""
plugins/discovery/mixed_archive_router.py - Heterogeneous Mixed Archive Router Plugin
========================================================================================
Stage 1 Discovery plugin that acts as core traffic router for heterogeneous archives,
assigning parser routes per file extension/type.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from ..base import BaseDiscoveryPlugin, MatchResult
from ..context import PipelineContext, FileInventoryItem
from ..registry import register_plugin

logger = logging.getLogger(__name__)

PARSER_ROUTE_MAP = {
    ".csv": "csv_parser",
    ".tsv": "csv_parser",
    ".xlsx": "scada_excel_parser",
    ".xls": "scada_excel_parser",
    ".h5": "hdf5_parser",
    ".hdf5": "hdf5_parser",
    ".mat": "mat_parser",
    ".parquet": "parquet_parser",
    ".txt": "txt_parser",
}


@register_plugin
class MixedArchiveRouterPlugin(BaseDiscoveryPlugin):
    plugin_id = "mixed_archive_router"
    plugin_name = "Mixed Archive Router Plugin"
    version = "1.0.0"
    stage = "discovery"
    priority = 12

    def probe(self, context: PipelineContext) -> MatchResult:
        if not context.inventory:
            return MatchResult(supported=False, confidence=0.0, reasons=["Inventory is empty; cannot route parser types"])

        extensions = {item.format_ext.lower() for item in context.inventory}
        is_heterogeneous = (
            context.layout_type == "heterogeneous_mixed_archive" or len(extensions) > 1
        )

        if is_heterogeneous:
            return MatchResult(
                supported=True,
                confidence=0.92,
                reasons=[
                    f"Heterogeneous layout or multi-extension inventory ({sorted(list(extensions))}) detected"
                ],
                detected_family="mixed_archive",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["Archive inventory is not heterogeneous"])

    def discover(self, target_path: Path, context: PipelineContext) -> PipelineContext:
        routes: Dict[str, str] = {}
        unrouted: List[str] = []

        for item in context.inventory:
            ext = item.format_ext.lower()
            assigned_parser = PARSER_ROUTE_MAP.get(ext, "generic_parser")
            routes[item.relative_path] = assigned_parser

            if assigned_parser == "generic_parser":
                unrouted.append(item.relative_path)
            elif item.detected_role == "unknown":
                item.detected_role = "fact" if ext in {".csv", ".parquet", ".h5", ".mat"} else "dimension"

        context.layout_type = "heterogeneous_mixed_archive"

        audit_entry = {
            "plugin_id": self.plugin_id,
            "stage": self.stage,
            "routes": routes,
            "unrouted_files": unrouted,
            "total_routed": len(routes),
        }
        context.audits.append(audit_entry)
        logger.info(f"[MixedArchiveRouter] Assigned parser routes for {len(routes)} files")
        return context
