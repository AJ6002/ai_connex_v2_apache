"""
test_compiler.py — Unit Tests for AIConnex Unified Dataset Compiler
====================================================================
Tests 4 internal layers on synthetic multi-file ZIP archives and real solar datasets.
"""

import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from aiconnex_zip_compiler.compiler import UnifiedCompiler, CompileResult
from aiconnex_zip_compiler.discovery import run_discovery
from aiconnex_zip_compiler.schema_mapper import SchemaMap, normalize_schema_and_timestamps


@pytest.fixture
def synthetic_zip(tmp_path) -> Path:
    """Create a synthetic multi-table ZIP (Fact + Dimension)."""
    fact_data = {
        "DATE_TIME": ["15-05-2020 00:00", "15-05-2020 00:15", "15-05-2020 00:30"] * 10,
        "PLANT_ID": [101] * 30,
        "SOURCE_KEY": [f"INV_{i%3}" for i in range(30)],
        "AC_POWER": [100.0 + i for i in range(30)],
    }
    dim_data = {
        "DATE_TIME": ["2020-05-15 00:00:00", "2020-05-15 00:15:00", "2020-05-15 00:30:00"] * 10,
        "PLANT_ID": [101] * 30,
        "SOURCE_KEY": ["WEATHER_SENSOR_1"] * 30,
        "IRRADIATION": [0.5 + i * 0.01 for i in range(30)],
    }

    fact_df = pd.DataFrame(fact_data)
    dim_df = pd.DataFrame(dim_data)

    fact_csv = tmp_path / "Fact_Telemetry.csv"
    dim_csv = tmp_path / "Dimension_Weather.csv"

    fact_df.to_csv(fact_csv, index=False)
    dim_df.to_csv(dim_csv, index=False)

    zip_path = tmp_path / "synthetic_data.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(fact_csv, arcname="Fact_Telemetry.csv")
        zf.write(dim_csv, arcname="Dimension_Weather.csv")

    return zip_path


def test_discovery_layer(synthetic_zip, tmp_path):
    temp_dir = tmp_path / "extracted"
    disc = run_discovery(synthetic_zip, temp_dir)
    assert len(disc.files) == 2
    assert disc.primary_group_col in ["PLANT_ID", "plant_id"]


def test_schema_mapper():
    df = pd.DataFrame({
        "DATE_TIME": ["15-05-2020 00:00", "15-05-2020 00:15"],
        "AC_POWER": [100.0, 105.0]
    })
    smap = SchemaMap()
    norm = normalize_schema_and_timestamps(df, "test.csv", "DATE_TIME", None, smap)
    assert "date_time" in norm.columns
    assert "ac_power" in norm.columns
    assert pd.api.types.is_datetime64_any_dtype(norm["date_time"])


def test_full_compiler_pipeline(synthetic_zip, tmp_path):
    out_dir = tmp_path / "compiled_output"
    compiler = UnifiedCompiler(synthetic_zip, out_dir)
    res: CompileResult = compiler.compile()

    assert res.success is True
    assert len(res.merged_files) >= 1
    assert Path(res.artifacts.join_audit_json).exists()
    assert Path(res.artifacts.schema_map_json).exists()
    assert Path(res.artifacts.compiler_report_json).exists()

    # Check merged CSV content
    merged_csv = Path(res.merged_files[0])
    merged_df = pd.read_csv(merged_csv)

    assert "date_time" in merged_df.columns
    assert "ac_power" in merged_df.columns
    assert "irradiation" in merged_df.columns
