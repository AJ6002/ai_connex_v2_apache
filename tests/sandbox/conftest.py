"""
Pytest configuration and fixtures for Level 4 Sandbox integration tests.
"""

from pathlib import Path

import pytest

from sandbox.docker_job_manager import DockerJobManager


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_job_dirs(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    return input_dir, output_dir


@pytest.fixture
def job_manager():
    return DockerJobManager()
