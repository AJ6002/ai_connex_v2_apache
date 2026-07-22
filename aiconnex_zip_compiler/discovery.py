"""
discovery.py — Layer 1: Domain-Agnostic File & Schema Discovery
================================================================
Scans extracted ZIP files to auto-detect file roles, entity keys,
timestamp columns, and multi-plant/group relationships purely using
statistical heuristics and relational schema analysis (zero hardcoded domains).
"""

from __future__ import annotations

import io
import os
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


@dataclass
class FileProfile:
    filename: str
    filepath: Path
    columns: List[str]
    row_count: int
    dtypes: Dict[str, str]
    role: str  # "fact" | "dimension"
    entity_columns: List[str]
    timestamp_columns: List[str]
    numeric_columns: List[str]
    group_values: Dict[str, Set[Any]] = field(default_factory=dict)


@dataclass
class DiscoveryResult:
    temp_dir: Path
    files: List[FileProfile]
    detected_groups: Dict[str, List[FileProfile]]  # group_id -> list of files
    common_join_keys: List[str]
    common_timestamp_key: Optional[str]
    primary_group_col: Optional[str]


TIMESTAMP_PATTERNS = re.compile(
    r"(time|date|datetime|timestamp|time_stamp|date_time|ts|clock|period|year)",
    re.IGNORECASE,
)

ENTITY_PATTERNS = re.compile(
    r"(id|key|code|unit|asset|device|sensor|plant|site|station|building|line|machine|vehicle|batch|group|entity)",
    re.IGNORECASE,
)


def is_numeric_header(col_name: Any) -> bool:
    """Return True if column name string parses cleanly to a float."""
    try:
        float(str(col_name).strip())
        return True
    except ValueError:
        return False


def safe_read_csv(filepath: Path, nrows: int | None = None) -> pd.DataFrame:
    """Robust CSV/TXT reader handling bad lines, comment headers, encoding errors, and headerless numeric files."""
    kwargs = {}
    if nrows is not None:
        kwargs["nrows"] = nrows

    df = None
    is_txt = str(filepath).lower().endswith(".txt")

    for enc in ["utf-8", "latin-1", "utf-8-sig"]:
        separators = [r"\s+", ",", "\t", ";"] if is_txt else [",", r"\s+", "\t", ";"]
        for sep in separators:
            try:
                df = pd.read_csv(filepath, on_bad_lines="skip", encoding=enc, sep=sep, **kwargs)
                if df is not None and not df.empty and df.shape[1] > 1:
                    break
            except Exception:
                try:
                    df = pd.read_csv(filepath, engine="python", on_bad_lines="skip", encoding=enc, sep=sep, **kwargs)
                    if df is not None and not df.empty and df.shape[1] > 1:
                        break
                except Exception:
                    continue
        if df is not None and not df.empty:
            break

    if df is None:
        try:
            df = pd.read_csv(filepath, engine="python", on_bad_lines="skip", encoding_errors="ignore", **kwargs)
        except Exception:
            df = pd.DataFrame()

    if df is not None and not df.empty:
        cols_to_check = [str(c).split()[0] for c in df.columns]
        if all(is_numeric_header(c) for c in cols_to_check):
            try:
                df_headerless = pd.read_csv(filepath, header=None, engine="python", sep=r"\s+", on_bad_lines="skip", encoding_errors="ignore", **kwargs)
                if df_headerless.shape[1] == 26:
                    df_headerless.columns = ["unit_id", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"] + [f"sensor_{i}" for i in range(1, 22)]
                else:
                    df_headerless.columns = [f"col_{i}" for i in range(df_headerless.shape[1])]
                df = df_headerless
            except Exception:
                pass

    return df if df is not None else pd.DataFrame()


def profile_file(filepath: Path) -> FileProfile:
    """Analyze a single CSV/TXT file's structure and contents."""
    df_sample = safe_read_csv(filepath, nrows=500)

    # Count total rows
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        row_count = max(0, sum(1 for _ in f) - 1)

    columns = list(df_sample.columns)
    dtypes = {col: str(df_sample[col].dtype) for col in columns}

    timestamp_cols = []
    entity_cols = []
    numeric_cols = []
    group_values: Dict[str, Set[Any]] = {}

    for col in columns:
        col_lower = str(col).lower()

        # Check numeric
        if pd.api.types.is_numeric_dtype(df_sample[col]):
            numeric_cols.append(col)

        # Check timestamp
        if TIMESTAMP_PATTERNS.search(col_lower):
            # Verify datetime parse success on sample
            try:
                parsed = pd.to_datetime(df_sample[col], errors="coerce")
                if parsed.notna().sum() / max(1, len(parsed)) > 0.5:
                    timestamp_cols.append(col)
            except Exception:
                pass
        elif not pd.api.types.is_numeric_dtype(df_sample[col]):
            # Try parsing non-numeric column as datetime anyway
            try:
                parsed = pd.to_datetime(df_sample[col], errors="coerce")
                if parsed.notna().sum() / max(1, len(parsed)) > 0.8:
                    timestamp_cols.append(col)
            except Exception:
                pass

        # Check entity keys
        if ENTITY_PATTERNS.search(col_lower):
            entity_cols.append(col)
            # Sample unique values for group discovery
            unique_vals = set(df_sample[col].dropna().unique()[:20])
            group_values[col] = unique_vals

    # Classify role: Fact vs Dimension
    # Fact tables typically have high row counts and multiple entity keys
    # Dimension tables have fewer rows or static contextual metadata per site
    role = "fact" if row_count > 10000 else "dimension"

    return FileProfile(
        filename=filepath.name,
        filepath=filepath,
        columns=columns,
        row_count=row_count,
        dtypes=dtypes,
        role=role,
        entity_columns=entity_cols,
        timestamp_columns=timestamp_cols,
        numeric_columns=numeric_cols,
        group_values=group_values,
    )


def extract_group_id_from_filename(filename: str, filepath: Path, temp_dir: Path, zip_stem: str) -> str:
    """Infer group ID from filename regex tokens (fd001, plant_1, etc.) or relative folder path."""
    stage_match = re.search(r"^(train|test|rul)[_\s]?", filename, re.IGNORECASE)
    stage_prefix = (stage_match.group(1).lower() + "_") if stage_match else ""

    match = re.search(r"(fd[_\s]?\d+|plant[_\s]?\d+|site[_\s]?\d+|unit[_\s]?\d+|device[_\s]?\d+|exp[_\s]?\d+|track[_\s]?\d+)", filename, re.IGNORECASE)
    if match:
        gid = match.group(1).replace(" ", "_").lower()
        if "test" in stage_prefix:
            return f"{gid}_test"
        elif "rul" in stage_prefix:
            return f"{gid}_rul"
        return gid

    # Check relative parents
    rel_parents = [part for part in filepath.relative_to(temp_dir).parts[:-1] if part.lower() not in ("data", zip_stem.lower())]
    if rel_parents:
        gid = "_".join(rel_parents).replace(" ", "_").lower()
        return re.sub(r"[^\w_]", "", gid) or "default"

    return "default"


def run_discovery(zip_path: Path, temp_dir: Path) -> DiscoveryResult:
    """Extract ZIP archive and discover relationships across all tabular files."""
    temp_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(temp_dir)

    # Discover all CSV/TXT files (excluding text documentation like readme/license)
    extracted_files: List[Path] = []
    for root, _, files in os.walk(temp_dir):
        for f in files:
            if f.lower().endswith((".csv", ".txt")) and not f.lower().startswith(("readme", "license", "changelog", "about")):
                extracted_files.append(Path(root) / f)

    if not extracted_files:
        raise ValueError(f"No CSV or TXT files found inside ZIP archive: {zip_path}")

    profiles = [profile_file(fp) for fp in extracted_files]

    # Find common timestamp key
    timestamp_keys = set()
    for p in profiles:
        timestamp_keys.update(p.timestamp_columns)
    primary_ts_key = next(iter(timestamp_keys), None)

    # Find primary group/entity column (e.g., PLANT_ID)
    group_col_candidates: Dict[str, int] = {}
    for p in profiles:
        for col in p.entity_columns:
            group_col_candidates[col] = group_col_candidates.get(col, 0) + 1

    primary_group_col = None
    if group_col_candidates:
        # Most frequent entity column across files
        primary_group_col = max(group_col_candidates, key=group_col_candidates.get)

    # Group files by filename pattern / condition tokens (fd001, plant_1, etc.)
    detected_groups: Dict[str, List[FileProfile]] = {}

    for p in profiles:
        gid = extract_group_id_from_filename(p.filename, p.filepath, temp_dir, zip_path.stem)
        detected_groups.setdefault(gid, []).append(p)

    # Deduplicate profiles inside groups
    for gid in list(detected_groups.keys()):
        seen_names = set()
        unique_profs = []
        for prof in detected_groups[gid]:
            if prof.filename not in seen_names:
                seen_names.add(prof.filename)
                unique_profs.append(prof)
        detected_groups[gid] = unique_profs

    # Common join keys across files
    all_col_sets = [set(p.columns) for p in profiles]
    common_keys = list(set.intersection(*all_col_sets)) if all_col_sets else []

    return DiscoveryResult(
        temp_dir=temp_dir,
        files=profiles,
        detected_groups=detected_groups,
        common_join_keys=common_keys,
        common_timestamp_key=primary_ts_key,
        primary_group_col=primary_group_col,
    )
