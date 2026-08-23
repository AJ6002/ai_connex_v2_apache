"""
Unit tests for Level 4 Sandbox & Segmentation contracts.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from contracts.discovery import DatasetDiscoveryArtifact
from contracts.sandbox import ParserResultManifest
from contracts.segmentation import CandidateRegion, SegmentationProposal


def test_candidate_region_valid():
    region = CandidateRegion(
        source_file="test.csv",
        row_start=0,
        row_end=50,
        col_start=0,
        col_end=5,
        detected_header=["timestamp", "device_id", "value"],
        matched_vocabulary=["timestamp", "device_id", "measurement"],
        confidence=0.95,
        proposed_table_name="telemetry_events",
        adjudication_log=["Matched 3/3 headers against standard registry"]
    )
    assert region.confidence == 0.95
    assert region.row_end == 50
    assert region.proposed_table_name == "telemetry_events"


def test_candidate_region_invalid_confidence():
    with pytest.raises(ValidationError):
        CandidateRegion(
            source_file="test.csv",
            row_start=0,
            row_end=10,
            col_start=0,
            col_end=2,
            confidence=1.5,  # > 1.0 invalid
            proposed_table_name="invalid"
        )


def test_segmentation_proposal_valid():
    region = CandidateRegion(
        source_file="htds_ltda.csv",
        row_start=3,
        row_end=100,
        col_start=0,
        col_end=10,
        confidence=0.92,
        proposed_table_name="htds_data"
    )
    proposal = SegmentationProposal(
        asset_id="asset_12345",
        regions=[region],
        requires_adjudication=False,
        adjudication_threshold=0.85
    )
    assert proposal.asset_id == "asset_12345"
    assert len(proposal.regions) == 1
    assert proposal.requires_adjudication is False


def test_parser_result_manifest_valid():
    now = datetime.utcnow()
    manifest = ParserResultManifest(
        job_id="job_8899",
        image_name="parser-csv",
        image_digest="sha256:1234567890abcdef",
        input_file="/sandbox/input/data.csv",
        input_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        output_parquet="/sandbox/output/data.parquet",
        output_hash="f1d2d2f924e986ac86fdf7b36c94bcdf32beec15",
        row_count=1000,
        schema_definition={"timestamp": "timestamp[us]", "val": "double"},
        started_at=now,
        completed_at=now,
        lineage={"chunk_size": 10000}
    )
    assert manifest.row_count == 1000
    assert manifest.quarantined is False


def test_dataset_discovery_artifact_with_segmentation():
    proposal = SegmentationProposal(
        asset_id="asset_99",
        regions=[],
        requires_adjudication=True
    )
    artifact = DatasetDiscoveryArtifact(
        asset_id="asset_99",
        member_inventory=["data.csv"],
        segmentation_proposal=proposal
    )
    assert artifact.segmentation_proposal is not None
    assert artifact.segmentation_proposal.requires_adjudication is True
