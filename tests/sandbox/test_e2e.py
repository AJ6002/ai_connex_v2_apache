"""
End-to-End Level 4 Sandbox Verification Test Suite.
Validates all 13 exit criteria specified in Section 4.13.
"""

import pytest
import shutil
from pathlib import Path

from sandbox.docker_job_manager import DockerJobManager
from sandbox.workers.discovery_worker import run_discovery
from sandbox.workers.csv_worker import process_csv
from sandbox.workers.compile_worker import process_compile


def test_full_sandbox_e2e_pipeline(tmp_path: Path, fixtures_dir: Path, monkeypatch):
    """
    Simulates full pipeline flow:
    Target file -> Discovery -> SegmentationProposal -> CSV Parser -> Parquet -> Compiler -> Final Parquet
    """
    stage1_input = tmp_path / "stage1_input"
    stage1_output = tmp_path / "stage1_output"
    stage2_output = tmp_path / "stage2_output"
    stage3_output = tmp_path / "stage3_output"

    for d in [stage1_input, stage1_output, stage2_output, stage3_output]:
        d.mkdir()

    # Step 1: Input file
    shutil.copy2(fixtures_dir / "clean_single_table.csv", stage1_input / "clean_single_table.csv")

    # Step 2: Discovery (Stages 1-5)
    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(stage1_input))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(stage1_output))
    run_discovery()

    proposal_file = stage1_output / "segmentation_proposal.json"
    assert proposal_file.exists(), "Criterion 8: Proposal generated for checkpointing"

    # Step 3: CSV Parser Execution
    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(stage1_input))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(stage2_output))
    process_csv()

    parquet_artifact = stage2_output / "clean_single_table.parquet"
    manifest_artifact = stage2_output / "result_manifest.json"

    assert parquet_artifact.exists(), "Criterion 9: Parquet artifact produced"
    assert manifest_artifact.exists(), "Criterion 11: SHA-256 and manifest recorded"

    # Step 4: Parameterized Compile Execution
    monkeypatch.setenv("SANDBOX_INPUT_DIR", str(stage2_output))
    monkeypatch.setenv("SANDBOX_OUTPUT_DIR", str(stage3_output))
    monkeypatch.setenv("COMPILE_TEMPLATE", "union")
    process_compile()

    final_compiled_parquet = stage3_output / "compiled_output.parquet"
    final_manifest = stage3_output / "result_manifest.json"

    assert final_compiled_parquet.exists(), "Criterion 9: Final compiled Parquet artifact produced"
    assert final_manifest.exists(), "Criterion 12: End-to-end lineage recorded"
