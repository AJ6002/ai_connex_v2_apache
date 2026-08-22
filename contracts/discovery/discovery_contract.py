from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from contracts.segmentation.segmentation_contract import SegmentationProposal


class DatasetDiscoveryArtifact(BaseModel):
    asset_id: str = Field(..., description="Target upload asset ID")
    archive_type: Optional[str] = Field(None, description="Archive extension (zip, tar, gz, none)")
    member_inventory: List[str] = Field(default_factory=list, description="List of archive member paths")
    member_sizes: Dict[str, int] = Field(default_factory=dict, description="Uncompressed member sizes")
    detected_formats: List[str] = Field(default_factory=list, description="Candidate formats detected (csv, xlsx, json)")
    candidate_timestamp_fields: List[str] = Field(default_factory=list, description="Discovered timestamp column names")
    candidate_identifier_fields: List[str] = Field(default_factory=list, description="Discovered asset/entity ID columns")
    sample_headers: Dict[str, List[str]] = Field(default_factory=dict, description="Header column names per member file")
    security_findings: List[str] = Field(default_factory=list, description="Security warnings (e.g. symlink detected, traversal rejected)")
    segmentation_proposal: Optional[SegmentationProposal] = Field(None, description="Typed segmentation proposal for candidate region boundaries")
    is_safe: bool = Field(default=True, description="Whether discovery passed security checks")

