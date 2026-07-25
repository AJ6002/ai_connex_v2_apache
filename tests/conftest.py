"""
conftest.py - Global pytest fixtures (G-12 Fix)
=================================================
Provides reusable synthetic DataFrames, manifest templates, and temporary workspace
fixtures across unit, matrix, contract, and scenario tests.
"""

import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd


@pytest.fixture
def synthetic_tabular_df():
    """Returns a synthetic 100-row tabular regression DataFrame."""
    np.random.seed(42)
    return pd.DataFrame({
        "feature_1": np.random.randn(100),
        "feature_2": np.random.randn(100),
        "feature_3": np.random.randn(100),
        "target": np.random.randn(100) * 10 + 50,
    })


@pytest.fixture
def synthetic_time_series_df():
    """Returns a synthetic 120-row multi-asset time series DataFrame."""
    np.random.seed(42)
    rows = []
    for unit in range(1, 5):  # 4 engines
        for cycle in range(1, 31):
            rows.append({
                "unit": unit,
                "cycle": cycle,
                "s1": np.random.randn(),
                "s2": np.random.randn(),
                "s3": np.random.randn(),
                "RUL": float(100 - cycle),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def sample_manifest(tmp_path):
    """Returns a standard manifest dictionary and saves a temporary JSON copy."""
    manifest = {
        "pipeline_run_id": "test_run_001",
        "ml_task": "regression",
        "data_topology": "multi_entity_time_series",
        "schema_config": {
            "entity_column": "unit",
            "timestamp_column": "cycle",
            "raw_features": ["s1", "s2", "s3"],
        },
        "label_contract": {
            "target_column": "RUL",
            "target_type": "time_to_event",
            "regime": "continuous",
        },
        "features_config": {
            "lag_features": True,
            "spectral_features": False,
            "normalization": "global",
        },
        "hpo_config": {
            "n_iter": 5,
            "scoring": "neg_root_mean_squared_error",
        },
        "candidate_algorithms": ["RandomForest", "LinearRegression"],
        "validation_gates": {
            "vg_1": {"min_train_rows": 10},
            "vg_2": {"r2_min": 0.5, "rmse_threshold": 20.0},
        },
    }
    manifest_file = tmp_path / "test_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    manifest["paths"] = {"manifest_self": str(manifest_file)}
    return manifest
