"""
Unit tests for Data Quality Verifier & Promotion Gates.
"""

import importlib.util
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

_file_path = Path(__file__).resolve().parent.parent.parent / "data-studio" / "quality" / "gx_verifier.py"
_spec = importlib.util.spec_from_file_location("gx_verifier_mod", _file_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load module from {_file_path}")
gx_verifier_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gx_verifier_mod)

DataQualityVerifier = gx_verifier_mod.DataQualityVerifier
DataQualityResult = gx_verifier_mod.DataQualityResult


def test_quality_verifier_clean_parquet():
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "clean_data.parquet"
        table = pa.table({
            "timestamp": ["2026-01-01T00:00:00", "2026-01-01T01:00:00"],
            "vibration": [1.2, 1.4],
            "temperature": [45.0, 46.2]
        })
        pq.write_table(table, parquet_path)

        verifier = DataQualityVerifier(max_null_threshold_pct=5.0)
        res = verifier.verify_parquet_artifact("asset-clean", str(parquet_path))

        assert isinstance(res, DataQualityResult)
        assert res.is_valid is True
        assert res.total_rows == 2
        assert res.total_columns == 3
        assert res.null_percentages["vibration"] == 0.0


def test_quality_verifier_high_nulls_rejection():
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "dirty_data.parquet"
        table = pa.table({
            "timestamp": ["2026-01-01T00:00:00", "2026-01-01T01:00:00"],
            "sensor_val": [None, None]  # 100% nulls
        })
        pq.write_table(table, parquet_path)

        verifier = DataQualityVerifier(max_null_threshold_pct=5.0)
        res = verifier.verify_parquet_artifact("asset-dirty", str(parquet_path))

        assert res.is_valid is False
        assert res.null_percentages["sensor_val"] == 100.0
        assert len(res.validation_findings) > 0
