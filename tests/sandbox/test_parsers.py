"""
Integration tests for CSV, XLSX, and Parquet parser sandbox workers.
"""

import shutil
from pathlib import Path

from sandbox.workers.csv_worker import process_csv
from sandbox.workers.parquet_worker import process_parquet


def test_csv_worker_standalone(tmp_path: Path, fixtures_dir: Path, monkeypatch):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    shutil.copy2(fixtures_dir / "clean_single_table.csv", input_dir / "clean_single_table.csv")

    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(input_dir))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(output_dir))

    process_csv()

    parquet_out = output_dir / "clean_single_table.parquet"
    manifest_out = output_dir / "result_manifest.json"

    assert parquet_out.exists()
    assert manifest_out.exists()


def test_parquet_worker_standalone(tmp_path: Path, fixtures_dir: Path, monkeypatch):
    # First generate a parquet file using csv worker
    input_dir = tmp_path / "input_csv"
    csv_out_dir = tmp_path / "parquet_input"
    input_dir.mkdir()
    csv_out_dir.mkdir()

    shutil.copy2(fixtures_dir / "clean_single_table.csv", input_dir / "clean_single_table.csv")

    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(input_dir))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(csv_out_dir))
    process_csv()

    # Now run parquet worker on generated parquet file
    pq_final_out = tmp_path / "pq_out"
    pq_final_out.mkdir()

    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(csv_out_dir))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(pq_final_out))

    process_parquet()

    assert (pq_final_out / "clean_single_table.parquet").exists()
    assert (pq_final_out / "result_manifest.json").exists()
