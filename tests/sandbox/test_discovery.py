"""
Integration tests for parser-discovery sandbox worker.
"""

import pytest
import shutil
from pathlib import Path
from sandbox.workers.discovery_worker import run_discovery


def test_discovery_worker_standalone(tmp_path: Path, fixtures_dir: Path, monkeypatch):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    # Copy fixture file
    src = fixtures_dir / "htds_ltda_stacked.csv"
    shutil.copy2(src, input_dir / "htds_ltda_stacked.csv")

    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(input_dir))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(output_dir))

    run_discovery()

    proposal_path = output_dir / "segmentation_proposal.json"
    discovery_path = output_dir / "discovery_artifact.json"

    assert proposal_path.exists()
    assert discovery_path.exists()
