"""
_shared.py — helpers shared by the 8+1 Scout analysis nodes.

Keeps DataFrame loading, safe row-count / sampling, and dtype-string
formatting in one place so no node has to redo them.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def compiled_csv_path_from_state(state) -> Optional[str]:
    """Extract the compiled CSV path from state, tolerating both the typed
    StructureAnalysis object and the legacy DIC dict shape."""
    sa = getattr(state, "structure_analysis", None)
    if sa is not None:
        # Pydantic model
        path = getattr(sa, "compiled_csv_path", None)
        if isinstance(sa, dict):
            path = sa.get("compiled_csv_path")
        if path:
            return str(path)

    # Legacy fallback: DIC dict shape
    dic = getattr(state, "dic", None)
    if dic is not None:
        if hasattr(dic, "compiled_dataset"):
            cds = dic.compiled_dataset
            path = getattr(cds, "combined_csv_path", None)
            if path:
                return str(path)
        if isinstance(dic, dict):
            cds = dic.get("compiled_dataset", {})
            path = cds.get("combined_csv_path") if isinstance(cds, dict) else None
            if path:
                return str(path)
    return None


def load_compiled_dataframe(state, sample_rows: Optional[int] = None):
    """Load the compiled CSV produced by structure_analysis_node as a DataFrame.
    If sample_rows is set and the file is larger than that, take a deterministic
    head+tail+random-middle sample so the analysis stays bounded.
    """
    import pandas as pd

    path = compiled_csv_path_from_state(state)
    if not path or not Path(path).exists():
        logger.warning(f"[Scout._shared] Compiled CSV not found at {path!r}")
        return None

    # Quick row count without a full load
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            total_rows = sum(1 for _ in f) - 1
    except Exception:
        total_rows = -1

    if sample_rows is None or total_rows <= sample_rows or total_rows < 0:
        return pd.read_csv(path, low_memory=False)

    # Deterministic sampling for large datasets
    head_n = sample_rows // 3
    tail_n = sample_rows // 3
    mid_n = sample_rows - head_n - tail_n
    logger.info(
        f"[Scout._shared] Sampling {sample_rows} rows from {total_rows}-row dataset "
        f"(head={head_n}, mid={mid_n}, tail={tail_n})"
    )
    head_df = pd.read_csv(path, low_memory=False, nrows=head_n)
    all_df = pd.read_csv(path, low_memory=False)
    # deterministic stratified pick from the middle
    if len(all_df) > head_n + tail_n and mid_n > 0:
        mid_range = all_df.iloc[head_n : len(all_df) - tail_n]
        step = max(1, len(mid_range) // mid_n)
        mid_df = mid_range.iloc[::step].head(mid_n)
    else:
        mid_df = all_df.iloc[0:0]
    tail_df = all_df.tail(tail_n)
    return pd.concat([head_df, mid_df, tail_df], ignore_index=True)


def hash_file(path: Path, chunk_size: int = 65536) -> str:
    """SHA-256 of a file's contents, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def dtype_str(series) -> str:
    """Compact dtype label, matching what the analysis manifests expect."""
    import pandas as pd
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "bool"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_categorical_dtype(series):
        return "categorical"
    return "text"
