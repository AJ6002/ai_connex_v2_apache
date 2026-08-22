"""
Integration tests for parser-compile DataFusion worker.
"""

import pytest
import shutil
from pathlib import Path
from sandbox.workers.csv_worker import process_csv
from sandbox.workers.compile_worker import process_compile


def test_compile_worker_standalone(tmp_path: Path, fixtures_dir: Path, monkeypatch):
    input_dir = tmp_path / "input_csv"
    pq_out_dir = tmp_path / "parquet_input"
    compile_out_dir = tmp_path / "compile_out"

    input_dir.mkdir()
    pq_out_dir.mkdir()
    compile_out_dir.mkdir()

    shutil.copy2(fixtures_dir / "clean_single_table.csv", input_dir / "clean_single_table.csv")

    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(input_dir))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(pq_out_dir))
    process_csv()

    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(pq_out_dir))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(compile_out_dir))
    monkeypatch.setenv("COMPILE_TEMPLATE", "union")

    process_compile()

    assert (compile_out_dir / "compiled_output.parquet").exists()
    assert (compile_out_dir / "result_manifest.json").exists()
