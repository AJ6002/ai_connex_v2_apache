"""
compiler.py — UnifiedCompiler Entry Point
==========================================
Orchestrates Layer 1 (Discovery) -> Layer 2 (Schema Mapping) ->
Layer 3 (Relational Join) -> Layer 4 (ML Handoff) for multi-file ZIP archives.
"""

from __future__ import annotations

import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from .discovery import run_discovery, DiscoveryResult, FileProfile
from .schema_mapper import SchemaMap, normalize_schema_and_timestamps
from .relational_joiner import perform_relational_join, JoinAudit
from .handoff import export_compiler_handoff, HandoffArtifacts


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
    Decoupled, domain-agnostic ingestion compiler for multi-file ZIP archives.

    Parameters
    ----------
    zip_path : str | Path
        Path to raw .zip file.
    output_dir : str | Path
        Destination folder for compiled CSVs and audit JSON files.
    """

    def __init__(self, zip_path: str | Path, output_dir: str | Path) -> None:
        self.zip_path = Path(zip_path).resolve()
        self.output_dir = Path(output_dir).resolve()

    def compile(self) -> CompileResult:
        """Execute all 4 layers sequentially."""
        t0 = time.time()
        temp_dir = Path(tempfile.mkdtemp(prefix="aic_compiler_"))

        try:
            # ── Layer 1: Discovery ───────────────────────────────────────────
            disc: DiscoveryResult = run_discovery(self.zip_path, temp_dir)

            schema_map = SchemaMap()
            merged_dfs: Dict[str, pd.DataFrame] = {}
            audits: List[JoinAudit] = []

            # ── Layer 2 & 3: Schema Mapping & Relational Join per Group ──────
            for group_id, profiles in disc.detected_groups.items():
                if not profiles:
                    continue

                # Separate Fact vs Dimension tables in this group
                fact_profs = [p for p in profiles if p.role == "fact"]
                dim_profs = [p for p in profiles if p.role == "dimension"]

                # If multiple fact profiles exist (e.g. parallel sensor channels), keep 1 primary fact and treat others as dim_profs for index-join
                if len(fact_profs) > 1:
                    primary_fact = max(fact_profs, key=lambda p: p.row_count)
                    extra_facts = [p for p in fact_profs if p != primary_fact]
                    dim_profs.extend(extra_facts)
                    fact_profs = [primary_fact]

                # Fallback: if no clear fact table, take largest file
                if not fact_profs:
                    fact_profs = [max(profiles, key=lambda p: p.row_count)]
                    dim_profs = [p for p in profiles if p != fact_profs[0]]

                fact_p = fact_profs[0]

                from .discovery import safe_read_csv

                # Load raw dataframes
                fact_df_raw = safe_read_csv(fact_p.filepath)
                fact_df = normalize_schema_and_timestamps(
                    fact_df_raw,
                    fact_p.filename,
                    disc.common_timestamp_key,
                    disc.primary_group_col,
                    schema_map,
                )

                dim_dfs_norm: List[Tuple[pd.DataFrame, str]] = []
                for dp in dim_profs:
                    dim_df_raw = safe_read_csv(dp.filepath)
                    dim_df = normalize_schema_and_timestamps(
                        dim_df_raw,
                        dp.filename,
                        disc.common_timestamp_key,
                        disc.primary_group_col,
                        schema_map,
                    )
                    dim_dfs_norm.append((dim_df, dp.filename))

                # Canonical join keys
                canonical_ts = schema_map.canonical_timestamp_col or "date_time"
                canonical_group = schema_map.canonical_group_col

                # ── Layer 3: Execute Join & Cartesian Guard ──────────────────
                merged, audit = perform_relational_join(
                    group_id=str(group_id),
                    fact_df=fact_df,
                    fact_filename=fact_p.filename,
                    dim_dfs=dim_dfs_norm,
                    ts_col=canonical_ts,
                    group_col=canonical_group,
                )

                merged_dfs[str(group_id)] = merged
                audits.append(audit)

            # ── Layer 4: ML Handoff & Artifact Export ────────────────────────
            duration = round(time.time() - t0, 3)
            artifacts = export_compiler_handoff(
                output_dir=self.output_dir,
                merged_dfs=merged_dfs,
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
            return CompileResult(
                input_zip=str(self.zip_path),
                output_dir=str(self.output_dir),
                merged_files=[],
                combined_file=None,
                artifacts=HandoffArtifacts({}, None, Path(""), Path(""), Path("")),
                audits=[],
                schema_map=SchemaMap(),
                duration_seconds=duration,
                success=False,
                error=str(e),
            )

        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
