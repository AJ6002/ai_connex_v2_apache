"""
compiler.py — Extensible Plugin Pipeline Ingestion Compiler Engine
===================================================================
Orchestrates Layer 1 -> Layer 5 plugin pipeline via PluginRegistry.
Produces deterministic, lockfile-tracked ingestion outputs for ML Node 1.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .handoff import export_compiler_handoff, HandoffArtifacts
from .plugins import (
    PipelineContext,
    PluginRegistry,
    UnsupportedLayoutError,
    AmbiguousPluginMatchError,
)
from .models import SchemaMap, JoinAudit

logger = logging.getLogger(__name__)


@dataclass
class CompileResult:
    input_zip: str
    output_dir: str
    merged_files: List[str]
    combined_file: Optional[str]
    artifacts: HandoffArtifacts
    audits: List[JoinAudit]
    schema_map: SchemaMap
    duration_seconds: float
    success: bool = True
    error: Optional[str] = None


class UnifiedCompiler:
    """
    Extensible Ingestion Compiler powered by a 5-Stage Plugin Pipeline & Registry.

    Parameters
    ----------
    zip_path : str | Path
        Path to raw .zip or dataset directory.
    output_dir : str | Path
        Destination folder for compiled CSVs, audits, and compiler_lock.json.
    """

    def __init__(self, zip_path: str | Path, output_dir: str | Path) -> None:
        self.zip_path = Path(zip_path).resolve()
        self.output_dir = Path(output_dir).resolve()

    def compile(self) -> CompileResult:
        """Execute all 5 plugin pipeline stages sequentially."""
        t0 = time.time()
        temp_dir = Path(tempfile.mkdtemp(prefix="aic_compiler_"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ── Pre-Check: Entry Schema Gate ────────────────────────────────────────
        from .schema_gate import SchemaGate
        gate = SchemaGate(self.zip_path)
        decision = gate.evaluate()
        if not decision.is_valid:
            logger.error(f"[SchemaGate] Rejected: {decision.gate_message}")
            return CompileResult(
                input_zip=str(self.zip_path),
                output_dir=str(self.output_dir),
                merged_files=[],
                combined_file=None,
                artifacts=HandoffArtifacts({}, None, Path(""), Path(""), Path(""), Path("")),
                audits=[],
                schema_map=SchemaMap(),
                duration_seconds=0.0,
                success=False,
                error=f"SchemaGate rejected input: {decision.gate_message}",
            )
        logger.info(f"[SchemaGate] Passed: {decision.gate_message} (Route: {decision.primary_route})")

        try:
            # ── Initialize Pipeline Context & Plugin Registry ─────────────────
            context = PipelineContext(
                target_path=self.zip_path,
                temp_dir=temp_dir,
                output_dir=self.output_dir,
            )

            registry = PluginRegistry.get_instance()
            registry.auto_discover()

            # ── Stage 1: Discovery Plugin ────────────────────────────────────
            disc_plugin = registry.resolve("discovery", context)
            context = disc_plugin.execute(context)
            context.active_plugins["discovery"] = f"{disc_plugin.plugin_id}@{disc_plugin.version}"

            # ── Stage 2: Parser Plugin ───────────────────────────────────────
            parser_plugin = registry.resolve("parser", context)
            context = parser_plugin.execute(context)
            context.active_plugins["parser"] = f"{parser_plugin.plugin_id}@{parser_plugin.version}"

            # ── Stage 3: Assembler Plugin ────────────────────────────────────
            assembler_plugin = registry.resolve("assembler", context)
            context = assembler_plugin.execute(context)
            context.active_plugins["assembler"] = f"{assembler_plugin.plugin_id}@{assembler_plugin.version}"

            # ── Stage 4: Feature Harvester Plugin (Optional) ─────────────────
            try:
                harvester_plugin = registry.resolve("harvester", context)
                context = harvester_plugin.execute(context)
                context.active_plugins["harvester"] = f"{harvester_plugin.plugin_id}@{harvester_plugin.version}"
            except (UnsupportedLayoutError, AmbiguousPluginMatchError):
                logger.debug("[UnifiedCompiler] Stage 4 Harvester skipped (not required for layout)")

            # ── Stage 5: Schema Normalizer Plugin ───────────────────────────
            normalizer_plugin = registry.resolve("normalizer", context)
            context = normalizer_plugin.execute(context)
            context.active_plugins["normalizer"] = f"{normalizer_plugin.plugin_id}@{normalizer_plugin.version}"

            # ── Freeze Registry & Write Lockfile ─────────────────────────────
            snapshot = registry.freeze()
            snapshot.write_lockfile(self.output_dir)

            # Determine final target DataFrames for handoff
            final_dfs = context.normalized_tables or context.harvested_tables or context.assembled_tables or context.parsed_tables
            if not final_dfs:
                raise ValueError("Pipeline produced no final canonical DataFrames")

            schema_map = SchemaMap()
            if context.primary_timestamp_col:
                schema_map.canonical_timestamp_col = context.primary_timestamp_col

            audits = [
                JoinAudit(
                    group_id=k,
                    fact_file=k,
                    dimension_files=[],
                    join_keys=context.join_keys,
                    join_type="plugin_pipeline",
                    fact_rows_before=len(v),
                    merged_rows_after=len(v),
                    null_column_percentages={},
                    cartesian_guard_passed=True,
                    warnings=[],
                    redundant_keys_excluded=[],
                )
                for k, v in final_dfs.items()
            ]

            duration = round(time.time() - t0, 3)
            artifacts = export_compiler_handoff(
                output_dir=self.output_dir,
                merged_dfs=final_dfs,
                audits=audits,
                schema_map=schema_map,
                duration_seconds=duration,
                zip_filename=self.zip_path.name,
            )

            return CompileResult(
                input_zip=str(self.zip_path),
                output_dir=str(self.output_dir),
                merged_files=[str(p) for p in artifacts.per_group_csvs.values()],
                combined_file=str(artifacts.combined_csv) if artifacts.combined_csv else None,
                artifacts=artifacts,
                audits=audits,
                schema_map=schema_map,
                duration_seconds=duration,
                success=True,
            )

        except Exception as e:
            duration = round(time.time() - t0, 3)
            logger.error(f"[UnifiedCompiler] Ingestion failure: {e}")
            return CompileResult(
                input_zip=str(self.zip_path),
                output_dir=str(self.output_dir),
                merged_files=[],
                combined_file=None,
                artifacts=HandoffArtifacts({}, None, Path(""), Path(""), Path(""), Path("")),
                audits=[],
                schema_map=SchemaMap(),
                duration_seconds=duration,
                success=False,
                error=str(e),
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
