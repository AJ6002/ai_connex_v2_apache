
from pydantic import BaseModel, Field

from contracts.segmentation.segmentation_contract import SegmentationProposal


class DatasetDiscoveryArtifact(BaseModel):
    asset_id: str = Field(..., description="Target upload asset ID")
    archive_type: str | None = Field(None, description="Archive extension (zip, tar, gz, none)")
    member_inventory: list[str] = Field(default_factory=list, description="List of archive member paths")
    member_sizes: dict[str, int] = Field(default_factory=dict, description="Uncompressed member sizes")
    detected_formats: list[str] = Field(default_factory=list, description="Candidate formats detected (csv, xlsx, json)")
    candidate_timestamp_fields: list[str] = Field(default_factory=list, description="Discovered timestamp column names")
    candidate_identifier_fields: list[str] = Field(default_factory=list, description="Discovered asset/entity ID columns")
    sample_headers: dict[str, list[str]] = Field(default_factory=dict, description="Header column names per member file")
    security_findings: list[str] = Field(default_factory=list, description="Security warnings (e.g. symlink detected, traversal rejected)")
    segmentation_proposal: SegmentationProposal | None = Field(None, description="Typed segmentation proposal for candidate region boundaries")
    is_safe: bool = Field(default=True, description="Whether discovery passed security checks")

