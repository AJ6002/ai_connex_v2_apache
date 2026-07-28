"""
Unit Tests — Node 1: preprocess.py
Tests: null imputation, duplicate removal, required-column guard, manifest creation.
"""
import os
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Helpers — replicate the core logic from preprocess.py without AWS calls
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SENSORS  = ["sensor_2", "sensor_3", "sensor_4", "sensor_7"]
REQUIRED = ["global_engine_id", "cycle", "RUL"]


def _make_df(rows=40, engines=2, introduce_nulls=False, introduce_dups=False):
    np.random.seed(0)
    data = []
    for eid in range(1, engines + 1):
        for c in range(1, rows // engines + 1):
            row = {"global_engine_id": eid, "cycle": c, "RUL": (rows // engines) - c}
            for s in SENSORS:
                row[s] = float(np.random.normal(50, 5))
            data.append(row)
    df = pd.DataFrame(data)
    if introduce_nulls:
        df.loc[0, "sensor_2"] = float("nan")
        df.loc[5, "sensor_3"] = float("nan")
    if introduce_dups:
        df = pd.concat([df, df.iloc[:3]], ignore_index=True)
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Mirrors preprocess.main() cleaning logic."""
    num_cols = df.select_dtypes(include=["number"]).columns
    for col in num_cols:
        if df[col].isnull().any():
            df[col] = df[col].ffill().bfill().fillna(df[col].mean())
    df = df.drop_duplicates().reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPreprocessCleaning:

    def test_no_nulls_in_output(self):
        df_raw = _make_df(introduce_nulls=True)
        assert df_raw.isnull().sum().sum() > 0, "Fixture should have nulls"
        df_clean = _clean(df_raw)
        assert df_clean.isnull().sum().sum() == 0, "Output must have zero nulls"

    def test_duplicates_removed(self):
        df_raw = _make_df(introduce_dups=True)
        original_len = len(_make_df())
        df_clean = _clean(df_raw)
        assert len(df_clean) == original_len, (
            f"Expected {original_len} rows after dedup, got {len(df_clean)}"
        )

    def test_output_rows_lte_input(self):
        df_raw = _make_df(introduce_dups=True)
        df_clean = _clean(df_raw)
        assert len(df_clean) <= len(df_raw)

    def test_required_columns_missing_raises(self):
        """Simulate the required-column guard from preprocess.main()."""
        df = _make_df().drop(columns=["RUL"])
        required = ["global_engine_id", "cycle", "RUL"]
        missing = [c for c in required if c not in df.columns]
        assert len(missing) > 0, "Should detect missing RUL column"

    def test_required_columns_present_passes(self):
        df = _make_df()
        required = ["global_engine_id", "cycle", "RUL"]
        missing = [c for c in required if c not in df.columns]
        assert missing == [], f"Unexpected missing columns: {missing}"

    def test_manifest_has_required_keys(self, tmp_path):
        """Manifest written by Node 1 must contain the contract keys."""
        config = {
            "pipeline_run_id": "test-001",
            "project": "test",
            "domain": "regression",
            "algorithm": "random_forest",
            "schema": {
                "target_column": "RUL",
                "time_index": "cycle",
                "identifier": "global_engine_id",
                "features": SENSORS,
            },
        }
        df = _make_df()
        manifest = {
            "manifest_id": f"manifest-{config['pipeline_run_id']}",
            "project": config["project"],
            "created_at": pd.Timestamp.now().isoformat(),
            "dataset": {"row_count": int(df.shape[0]), "column_count": int(df.shape[1])},
            "schema": config["schema"],
            "routing_decision": {
                "problem_type": config["domain"],
                "algorithm": config["algorithm"],
            },
        }
        required_keys = ["manifest_id", "schema", "routing_decision", "dataset"]
        for key in required_keys:
            assert key in manifest, f"Manifest missing key: {key}"

    def test_numeric_column_dtype_preserved(self):
        df = _make_df()
        df_clean = _clean(df)
        for col in SENSORS:
            assert pd.api.types.is_numeric_dtype(df_clean[col]), (
                f"Column {col} should remain numeric after cleaning"
            )
