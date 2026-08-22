"""
Segmentation Contracts - Typed boundary between discovery and plan validation.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CandidateRegion(BaseModel):
    source_file: str = Field(..., description="Path or name of the source file being segmented")
    row_start: int = Field(..., ge=0, description="0-indexed starting row of region")
    row_end: int = Field(..., ge=0, description="0-indexed ending row of region (inclusive)")
    col_start: int = Field(..., ge=0, description="0-indexed starting column of region")
    col_end: int = Field(..., ge=0, description="0-indexed ending column of region (inclusive)")
    detected_header: List[str] = Field(default_factory=list, description="Header column names detected for this region")
    matched_vocabulary: List[str] = Field(default_factory=list, description="Standardized vocabulary matches")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Segmentation confidence score (0.0 to 1.0)")
    proposed_table_name: str = Field(..., description="Proposed canonical table name for this region")
    adjudication_log: List[str] = Field(default_factory=list, description="Audit log of adjudication decisions")


class SegmentationProposal(BaseModel):
    asset_id: str = Field(..., description="Target dataset/upload asset ID")
    pipeline_version: str = Field(default="1.0.0", description="Pipeline contract version")
    regions: List[CandidateRegion] = Field(default_factory=list, description="Discovered candidate data regions")
    requires_adjudication: bool = Field(default=False, description="Flag indicating if low confidence requires human/LLM review")
    adjudication_threshold: float = Field(default=0.85, description="Confidence threshold triggering mandatory adjudication")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of proposal generation")
