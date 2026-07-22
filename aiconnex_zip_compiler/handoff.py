"""
handoff.py — Layer 4: ML Handoff & Artifact Exporter
=====================================================
Exports per-group merged CSVs, optional combined fleet table, join_audit.json,
schema_map.json, and compiler_report.json to the output workspace.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from .schema_mapper import SchemaMap
from .relational_joiner import JoinAudit


@dataclass
class HandoffArtifacts:
    per_group_csvs: Dict[str, Path]
    combined_csv: Optional[Path]
    join_audit_json: Path
    schema_map_json: Path
    compiler_report_json: Path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "per_group_csvs": {k: str(v) for k, v in self.per_group_csvs.items()},
            "combined_csv": str(self.combined_csv) if self.combined_csv else None,
            "join_audit_json": str(self.join_audit_json),
            "schema_map_json": str(self.schema_map_json),
            "compiler_report_json": str(self.compiler_report_json),
        }


def export_compiler_handoff(
    output_dir: Path,
    merged_dfs: Dict[str, pd.DataFrame],
    audits: List[JoinAudit],
    schema_map: SchemaMap,
    duration_seconds: float,
    zip_filename: str,
) -> HandoffArtifacts:
    """Write merged dataset CSVs and audit/schema JSON reports to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    per_group_csvs: Dict[str, Path] = {}
    all_dfs: List[pd.DataFrame] = []

    # 1. Export Per-Group Merged CSVs
    for group_id, df in merged_dfs.items():
        clean_gid = str(group_id).replace(" ", "_").lower()
        csv_path = output_dir / f"group_{clean_gid}_merged.csv"
        df.to_csv(csv_path, index=False)
        per_group_csvs[group_id] = csv_path

        # Prepare for vertical multi-entity concatenation (Gap 3 & 4)
        df_tagged = df.copy()
        id_col = "device_id" if "device" in clean_gid else "group_id"
        if id_col not in df_tagged.columns and "group_id" not in df_tagged.columns and "device_id" not in df_tagged.columns:
            df_tagged.insert(0, id_col, group_id)
        all_dfs.append(df_tagged)

    # 2. Export Combined Fleet/Multi-Device CSV (if multiple groups exist)
    combined_csv_path: Optional[Path] = None
    if len(all_dfs) > 1:
        combined_csv_path = output_dir / "all_groups_combined.csv"
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df.to_csv(combined_csv_path, index=False)

    # 3. Export join_audit.json
    join_audit_path = output_dir / "join_audit.json"
    audit_data = [a.to_dict() for a in audits]
    with open(join_audit_path, "w", encoding="utf-8") as f:
        json.dump({"audits": audit_data}, f, indent=2)

    # 4. Export schema_map.json
    schema_map_path = output_dir / "schema_map.json"
    with open(schema_map_path, "w", encoding="utf-8") as f:
        json.dump(schema_map.to_dict(), f, indent=2)

    # 5. Export compiler_report.json
    compiler_report_path = output_dir / "compiler_report.json"
    total_rows = sum(len(df) for df in merged_dfs.values())
    report_data = {
        "status": "success",
        "input_zip": zip_filename,
        "duration_seconds": duration_seconds,
        "total_output_rows": total_rows,
        "groups_processed": list(merged_dfs.keys()),
        "output_files": {
            "per_group": [str(p) for p in per_group_csvs.values()],
            "combined": str(combined_csv_path) if combined_csv_path else None,
        },
        "cartesian_explosion_guards_passed": all(a.cartesian_guard_passed for a in audits),
    }
    with open(compiler_report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    return HandoffArtifacts(
        per_group_csvs=per_group_csvs,
        combined_csv=combined_csv_path,
        join_audit_json=join_audit_path,
        schema_map_json=schema_map_path,
        compiler_report_json=compiler_report_path,
    )
