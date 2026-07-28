"""
batch_writer.py - Per-Partition Job Batch Emitter
==================================================
Implements the "one model per partition" output mode.

When the user chooses to build individual models (for example one model per
fault mode, per operating condition, per machine, or per site), the compiler
must not collapse everything into a single flat CSV. Instead it emits a
self-contained job directory per partition, plus a manifest describing the
batch so the downstream ML pipeline can fan out N training jobs.

Output layout:
    output_dir/
        batch_manifest.json
        jobs/
            <partition_id>/
                <table>.csv
                job_spec.json
            <partition_id>/
                ...

Partition assignment comes from the intelligence layer's detected partitions
(LLM-derived member_tables). Tables not claimed by any partition are written to
a "shared" job directory so dimension/lookup tables remain available to every
training job.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

SHARED_JOB_ID = "_shared"


@dataclass
class JobSpec:
    """One training job produced for a single partition."""

    job_id: str
    partition_id: str
    partition_label: str
    partition_dimension: Optional[str]
    table_files: Dict[str, str] = field(default_factory=dict)  # table_name -> relative csv path
    row_count: int = 0
    target_column: Optional[str] = None
    shared_table_files: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "partition_id": self.partition_id,
            "partition_label": self.partition_label,
            "partition_dimension": self.partition_dimension,
            "table_files": self.table_files,
            "shared_table_files": self.shared_table_files,
            "row_count": self.row_count,
            "target_column": self.target_column,
        }


@dataclass
class BatchResult:
    """Outcome of a per-partition batch export."""

    manifest_path: Path
    jobs_root: Path
    job_specs: List[JobSpec] = field(default_factory=list)
    all_csv_paths: List[Path] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_path": str(self.manifest_path),
            "jobs_root": str(self.jobs_root),
            "job_count": len(self.job_specs),
            "jobs": [j.to_dict() for j in self.job_specs],
        }


def _safe_id(text: str) -> str:
    """Filesystem-safe identifier."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("_")
    return slug.lower() or "partition"


def export_partition_batch(
    output_dir: Path,
    tables: Dict[str, pd.DataFrame],
    partitions: List[Dict[str, Any]],
    partition_dimension: Optional[str] = None,
    target_column: Optional[str] = None,
    dataset_name: str = "",
) -> Optional[BatchResult]:
    """
    Write one job directory per partition.

    Parameters
    ----------
    output_dir : Path
        Compiler output directory.
    tables : dict
        Final table name -> DataFrame (post assembly/normalization).
    partitions : list of dict
        [{group_id, group_label, member_tables}, ...] from the intelligence layer.
    partition_dimension : str, optional
        Plain-language name of what separates partitions (e.g. "fault mode").
    target_column : str, optional
        Target column the user's chosen intent implies, if any.
    dataset_name : str
        Source archive name, recorded in the manifest.

    Returns
    -------
    BatchResult or None
        None when there is nothing to partition (caller should fall back to
        single-merged output).
    """
    if not tables:
        logger.warning("[BatchWriter] No tables to export")
        return None

    if not partitions:
        logger.warning("[BatchWriter] No partitions provided - cannot emit job batch")
        return None

    output_dir = Path(output_dir)
    jobs_root = output_dir / "jobs"
    jobs_root.mkdir(parents=True, exist_ok=True)

    # Map each table to its partition. A table may legitimately be unclaimed
    # (dimension/lookup tables) - those go to the shared job.
    claimed: Dict[str, str] = {}
    for partition in partitions:
        group_id = str(partition.get("group_id", "")).strip()
        if not group_id:
            continue
        for table_name in partition.get("member_tables", []) or []:
            if table_name in tables:
                claimed[str(table_name)] = group_id

    unclaimed = [name for name in tables if name not in claimed]

    job_specs: List[JobSpec] = []
    all_csv_paths: List[Path] = []

    # -- Shared tables (available to every job) ----------------------------
    shared_files: Dict[str, str] = {}
    if unclaimed:
        shared_dir = jobs_root / SHARED_JOB_ID
        shared_dir.mkdir(parents=True, exist_ok=True)
        for table_name in unclaimed:
            df = tables[table_name]
            if df is None or df.empty:
                continue
            csv_path = shared_dir / f"{_safe_id(table_name)}.csv"
            df.to_csv(csv_path, index=False)
            all_csv_paths.append(csv_path)
            shared_files[table_name] = str(csv_path.relative_to(output_dir)).replace("\\", "/")

        if shared_files:
            logger.info(
                f"[BatchWriter] {len(shared_files)} shared table(s) written to {SHARED_JOB_ID}"
            )

    # -- One job per partition ---------------------------------------------
    for partition in partitions:
        group_id = str(partition.get("group_id", "")).strip()
        if not group_id:
            continue

        member_tables = [
            name for name in (partition.get("member_tables") or []) if name in tables
        ]
        if not member_tables:
            logger.debug(
                f"[BatchWriter] Partition '{group_id}' has no matching tables - skipped"
            )
            continue

        job_id = _safe_id(group_id)
        job_dir = jobs_root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        table_files: Dict[str, str] = {}
        row_count = 0

        for table_name in member_tables:
            df = tables[table_name]
            if df is None or df.empty:
                continue
            csv_path = job_dir / f"{_safe_id(table_name)}.csv"
            df.to_csv(csv_path, index=False)
            all_csv_paths.append(csv_path)
            table_files[table_name] = str(csv_path.relative_to(output_dir)).replace("\\", "/")
            row_count += len(df)

        if not table_files:
            continue

        spec = JobSpec(
            job_id=job_id,
            partition_id=group_id,
            partition_label=str(partition.get("group_label", group_id)),
            partition_dimension=partition_dimension,
            table_files=table_files,
            shared_table_files=shared_files,
            row_count=row_count,
            target_column=target_column,
        )

        # Per-job spec so each downstream training job is self-describing
        (job_dir / "job_spec.json").write_text(
            json.dumps(spec.to_dict(), indent=2), encoding="utf-8"
        )
        job_specs.append(spec)

    if not job_specs:
        logger.warning("[BatchWriter] No jobs produced - partitions matched no tables")
        return None

    # -- Batch manifest ----------------------------------------------------
    manifest = {
        "dataset_name": dataset_name,
        "output_mode": "per_partition_batch",
        "partition_dimension": partition_dimension,
        "job_count": len(job_specs),
        "target_column": target_column,
        "shared_tables": shared_files,
        "jobs": [spec.to_dict() for spec in job_specs],
        "downstream_instructions": (
            "Submit one training job per entry in 'jobs'. Each job directory "
            "contains its partition tables plus job_spec.json. Tables listed in "
            "'shared_tables' apply to every job."
        ),
    }

    manifest_path = output_dir / "batch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    logger.info(
        f"[BatchWriter] Emitted {len(job_specs)} job(s) partitioned by "
        f"'{partition_dimension or 'partition'}' -> {manifest_path}"
    )

    return BatchResult(
        manifest_path=manifest_path,
        jobs_root=jobs_root,
        job_specs=job_specs,
        all_csv_paths=all_csv_paths,
    )
