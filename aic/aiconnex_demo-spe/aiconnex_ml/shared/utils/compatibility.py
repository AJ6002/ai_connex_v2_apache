"""
compatibility.py — numpy/pandas type safety & version-safe metric wrappers
==========================================================================
Prevents JSON serialization errors and sklearn version conflicts.
"""

from __future__ import annotations
from typing import Any
import numpy as np


def to_python_type(val: Any) -> Any:
    """Cast numpy scalar types to native Python for JSON/logging safety."""
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    if isinstance(val, np.bool_):
        return bool(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    return val


def safe_dict(d: dict) -> dict:
    """Recursively cast all values in a dict to Python-native types."""
    return {k: to_python_type(v) if not isinstance(v, dict) else safe_dict(v)
            for k, v in d.items()}


def sklearn_version_tuple() -> tuple[int, int, int]:
    """Return sklearn version as a (major, minor, patch) tuple."""
    import sklearn
    parts = sklearn.__version__.split(".")
    return tuple(int(x) for x in parts[:3])


def r2_score_safe(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """R² score clamped to [-1, 1] to prevent extreme values on bad models."""
    from sklearn.metrics import r2_score
    score = r2_score(y_true, y_pred)
    return float(np.clip(score, -1.0, 1.0))
