"""
Interface to the real pipeline state (dataset registry, meta1/meta2/meta3
stage completion). This module is intentionally a thin, swappable layer --
today it reads from an in-memory dict standing in for your actual
Validation_Gateway backend; swap the function bodies for real DB/file/API
calls once this is wired to the real service, without touching anything
else in the chatbot backend.
"""

from typing import Optional

# In-memory stand-in for your real dataset registry / meta1/meta2/meta3
# tracking store. Replace with real lookups (DB, file store, or an internal
# API call to the Flask/Express validation backend).
_FAKE_REGISTRY: dict[str, dict] = {
    "sales_q3": {
        "profiled": True,
        "dag_matched": "DAG-91B-A",
        "dag_verified": True,
        "recipe_compiled": False,
        "algorithm_family": "regression",
    },
    "sensor_data.csv": {
        "profiled": False,
        "dag_matched": None,
        "dag_verified": False,
        "recipe_compiled": False,
        "algorithm_family": None,
    },
}


def dataset_exists(dataset_id: str) -> bool:
    return dataset_id in _FAKE_REGISTRY


def get_dataset_state(dataset_id: str) -> Optional[dict]:
    return _FAKE_REGISTRY.get(dataset_id)


def mark_stage_complete(dataset_id: str, stage: str, **fields) -> None:
    """Called by the dispatcher after (simulating) a real pipeline stage run."""
    entry = _FAKE_REGISTRY.setdefault(dataset_id, {})
    entry.update(fields)


def register_dataset(dataset_id: str) -> None:
    _FAKE_REGISTRY.setdefault(
        dataset_id,
        {"profiled": False, "dag_matched": None, "dag_verified": False, "recipe_compiled": False, "algorithm_family": None},
    )
