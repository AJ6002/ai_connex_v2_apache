"""
relational_joiner.py — Layer 3: Relational Join Engine & Cartesian Guard
========================================================================
Joins Fact (high cardinality time-series) and Dimension (environmental/contextual)
tables on composite entity and timestamp keys. Implements a strict Cartesian
Explosion Guard and deduplicates redundant source keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd


@dataclass
class JoinAudit:
    group_id: str
    fact_file: str
    dimension_files: List[str]
    join_keys: List[str]
    join_type: str
    fact_rows_before: int
    merged_rows_after: int
    null_column_percentages: Dict[str, float]
    cartesian_guard_passed: bool
    warnings: List[str] = field(default_factory=list)
    redundant_keys_excluded: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "fact_file": self.fact_file,
            "dimension_files": self.dimension_files,
            "join_keys": self.join_keys,
            "join_type": self.join_type,
            "fact_rows_before": self.fact_rows_before,
            "merged_rows_after": self.merged_rows_after,
            "null_column_percentages": self.null_column_percentages,
            "cartesian_guard_passed": self.cartesian_guard_passed,
            "warnings": self.warnings,
            "redundant_keys_excluded": self.redundant_keys_excluded,
        }


def perform_relational_join(
    group_id: str,
    fact_df: pd.DataFrame,
    fact_filename: str,
    dim_dfs: List[Tuple[pd.DataFrame, str]],
    ts_col: str,
    group_col: Optional[str],
) -> Tuple[pd.DataFrame, JoinAudit]:
    """
    Relationally join dimension tables onto the primary fact table for a single entity group.
    Applies Cartesian Explosion Guard and key deduplication.
    """
    fact_rows = len(fact_df)
    merged_df = fact_df.copy()
    dim_filenames = [fname for _, fname in dim_dfs]
    warnings = []
    redundant_keys_excluded = []
    join_keys_used = [ts_col]
    if group_col and group_col in fact_df.columns:
        join_keys_used.append(group_col)

    actual_join_keys = join_keys_used.copy()
    join_type = "exact_left_composite"

    for dim_df, dim_fname in dim_dfs:
        dim_clean = dim_df.copy()

        # Check join keys present in both merged fact table and dimension table
        actual_join_keys = [k for k in join_keys_used if k in dim_clean.columns and k in merged_df.columns]
        if not actual_join_keys:
            actual_join_keys = [ts_col] if (ts_col in dim_clean.columns and ts_col in merged_df.columns) else []

        if not actual_join_keys:
            # Check for Row-Aligned Index-Based Join fallback (Gap 1)
            if len(dim_clean) == len(fact_df):
                warnings.append(f"Index-joined {dim_fname} side-by-side (equal row count: {len(fact_df)}).")
                new_cols = [c for c in dim_clean.columns if c not in merged_df.columns]
                if new_cols:
                    merged_df = pd.concat([merged_df.reset_index(drop=True), dim_clean[new_cols].reset_index(drop=True)], axis=1)
                join_type = "index_aligned_concat"
                continue
            else:
                warnings.append(f"Skipped {dim_fname}: No matching join keys ({join_keys_used}) and row counts differ.")
                continue

        # Check for non-join entity keys in dimension table (e.g. weather source_key) that differ
        # Exclude redundant dimension entity keys from feature inputs by default
        dim_entity_cols = [
            c for c in dim_clean.columns
            if ("key" in c or "id" in c or "code" in c)
            and c not in actual_join_keys
        ]
        for red_col in dim_entity_cols:
            redundant_keys_excluded.append(f"{dim_fname}:{red_col}")
            dim_clean = dim_clean.drop(columns=[red_col], errors="ignore")

        # Deduplicate dimension table on join keys before merging
        dim_clean = dim_clean.drop_duplicates(subset=actual_join_keys)

        # Attempt exact left merge
        try:
            temp_merged = merged_df.merge(
                dim_clean,
                on=actual_join_keys,
                how="left",
                suffixes=("", f"_{dim_fname.split('.')[0].lower()}"),
            )
        except Exception:
            # Fallback to ASOF nearest time join if exact merge fails
            join_type = "asof_nearest_time"
            merged_sorted = merged_df.sort_values(ts_col)
            dim_sorted = dim_clean.sort_values(ts_col)
            by_cols = [k for k in actual_join_keys if k != ts_col]

            temp_merged = pd.merge_asof(
                merged_sorted,
                dim_sorted,
                on=ts_col,
                by=by_cols if by_cols else None,
                direction="nearest",
                tolerance=pd.Timedelta("30min"),
                suffixes=("", f"_{dim_fname.split('.')[0].lower()}"),
            )

        merged_df = temp_merged

    merged_rows = len(merged_df)

    # ── Cartesian Explosion Guard ─────────────────────────────────────────────
    # If row count grows by >5%, abort to prevent corrupted cross-join tables
    cartesian_passed = True
    if merged_rows > int(fact_rows * 1.05):
        cartesian_passed = False
        warnings.append(
            f"CRITICAL: Cartesian explosion detected! Fact rows: {fact_rows} -> Merged rows: {merged_rows}"
        )
        raise RuntimeError(
            f"Cartesian Explosion Guard triggered for group '{group_id}': "
            f"Row count exploded from {fact_rows} to {merged_rows}. Verify join keys."
        )

    # Calculate NULL percentage report
    null_pcts = (merged_df.isna().sum() / max(1, len(merged_df)) * 100).round(2).to_dict()

    audit = JoinAudit(
        group_id=group_id,
        fact_file=fact_filename,
        dimension_files=dim_filenames,
        join_keys=actual_join_keys,
        join_type=join_type,
        fact_rows_before=fact_rows,
        merged_rows_after=merged_rows,
        null_column_percentages=null_pcts,
        cartesian_guard_passed=cartesian_passed,
        warnings=warnings,
        redundant_keys_excluded=redundant_keys_excluded,
    )

    return merged_df, audit
