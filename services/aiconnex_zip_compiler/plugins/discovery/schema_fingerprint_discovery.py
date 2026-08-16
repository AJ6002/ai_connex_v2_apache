"""
plugins/discovery/schema_fingerprint_discovery.py - Schema Fingerprint & Jaccard Distance Plugin
================================================================================================
Stage 1 Discovery plugin that inspects tabular files, calculates column set similarities
using Jaccard distance, and classifies archive layout as same_schema_batch,
relational_schema_bundle, or heterogeneous_mixed_archive.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd

from ..base import BaseDiscoveryPlugin, MatchResult
from ..context import PipelineContext, FileInventoryItem
from ..registry import register_plugin

logger = logging.getLogger(__name__)

TABULAR_EXTENSIONS = {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".txt"}


def _jaccard_distance(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard distance D_J(A, B) = 1 - (|A intersect B| / |A union B|)."""
    if not set_a and not set_b:
        return 0.0
    union_len = len(set_a | set_b)
    if union_len == 0:
        return 0.0
    intersect_len = len(set_a & set_b)
    similarity = intersect_len / union_len
    return round(1.0 - similarity, 4)


def _extract_column_fingerprint(filepath: Path, ext: str) -> Set[str]:
    """Read top row of tabular file and return cleaned set of column header strings."""
    ext = ext.lower()
    try:
        if ext in {".csv", ".tsv", ".txt"}:
            sep = "\t" if ext == ".tsv" else ","
            df_head = pd.read_csv(filepath, nrows=1, sep=None, engine="python")
            return {str(c).strip() for c in df_head.columns}
        elif ext in {".xlsx", ".xls"}:
            df_head = pd.read_excel(filepath, nrows=1)
            return {str(c).strip() for c in df_head.columns}
        elif ext == ".parquet":
            df_head = pd.read_parquet(filepath)
            return {str(c).strip() for c in df_head.columns}
    except Exception as e:
        logger.warning(f"[SchemaFingerprint] Failed reading header for {filepath.name}: {e}")
    return set()


@register_plugin
class SchemaFingerprintDiscoveryPlugin(BaseDiscoveryPlugin):
    plugin_id = "schema_fingerprint_discovery"
    plugin_name = "Schema Fingerprint Discovery Plugin"
    version = "1.0.0"
    stage = "discovery"
    priority = 8

    def probe(self, context: PipelineContext) -> MatchResult:
        tabular_items = [
            item for item in context.inventory
            if item.format_ext.lower() in TABULAR_EXTENSIONS
        ]
        if tabular_items:
            return MatchResult(
                supported=True,
                confidence=0.88,
                reasons=[f"Tabular inventory ({len(tabular_items)} files) available for schema fingerprinting"],
                detected_family="schema_fingerprint",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No tabular files available in inventory"])

    def discover(self, target_path: Path, context: PipelineContext) -> PipelineContext:
        items = context.inventory
        if not items and target_path and target_path.exists():
            base_scan = target_path if target_path.is_dir() else target_path.parent
            items = [
                FileInventoryItem(
                    filepath=p,
                    relative_path=str(p.relative_to(base_scan)),
                    size_bytes=p.stat().st_size,
                    format_ext=p.suffix.lower(),
                )
                for p in base_scan.rglob("*") if p.is_file()
            ]

        tabular_items = [
            item for item in items
            if item.format_ext.lower() in TABULAR_EXTENSIONS
        ]

        fingerprints: Dict[str, Set[str]] = {}
        for item in tabular_items:
            cols = _extract_column_fingerprint(item.filepath, item.format_ext)
            if cols:
                fingerprints[item.relative_path] = cols

        if not fingerprints:
            logger.info("[SchemaFingerprint] No readable tabular column fingerprints extracted")
            context.layout_type = "heterogeneous_mixed_archive"
            return context

        paths = list(fingerprints.keys())
        distances: List[float] = []

        if len(paths) <= 1:
            mean_distance = 0.0
        else:
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    dist = _jaccard_distance(fingerprints[paths[i]], fingerprints[paths[j]])
                    distances.append(dist)
            mean_distance = round(sum(distances) / len(distances), 4)

        col_counts: Dict[str, int] = {}
        for cols in fingerprints.values():
            for c in cols:
                col_counts[c] = col_counts.get(c, 0) + 1

        join_key_candidates = [
            c for c, count in col_counts.items()
            if count >= 2
        ]

        if mean_distance <= 0.15:
            layout_type = "same_schema_batch"
        elif join_key_candidates:
            layout_type = "relational_schema_bundle"
        else:
            layout_type = "heterogeneous_mixed_archive"

        context.layout_type = layout_type
        if join_key_candidates and not context.join_keys:
            context.join_keys = sorted(join_key_candidates)

        audit_entry = {
            "plugin_id": self.plugin_id,
            "stage": self.stage,
            "layout_type": layout_type,
            "mean_jaccard_distance": mean_distance,
            "fingerprints": {k: sorted(list(v)) for k, v in fingerprints.items()},
            "join_key_candidates": sorted(join_key_candidates),
        }
        context.audits.append(audit_entry)
        logger.info(f"[SchemaFingerprint] Layout classified as '{layout_type}' (mean Jaccard distance={mean_distance})")
        return context
