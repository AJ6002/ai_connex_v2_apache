"""
Integration tests for DockerJobManager host orchestration security controls.
"""

import pytest
import shutil
from pathlib import Path

from sandbox.docker_job_manager import DockerJobManager


def test_job_manager_initialization():
    jm = DockerJobManager()
    assert jm.registry is not None
    assert "parser-csv" in jm.config["images"]


def test_job_manager_quarantine_handler(tmp_path: Path):
    jm = DockerJobManager()
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    # Create dummy failing file
    (input_dir / "bad.csv").write_text("invalid_data")

    jm._handle_quarantine("job_test_q1", input_dir, output_dir, "Test Quarantine Execution")

    quarantine_target = jm.quarantine_dir / "quarantine_job_test_q1"
    assert quarantine_target.exists()
    assert (quarantine_target / "quarantine_reason.txt").exists()
