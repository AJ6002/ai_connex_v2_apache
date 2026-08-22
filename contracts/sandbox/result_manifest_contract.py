"""
Sandbox Result Manifest Contract - Execution result record produced by signed parser images.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ParserResultManifest(BaseModel):
    job_id: str = Field(..., description="Unique host Job Manager job identifier")
    image_name: str = Field(..., description="Container image name used (e.g. parser-csv)")
    image_digest: str = Field(..., description="Immutable image sha256 digest")
    input_file: str = Field(..., description="Name or relative path of input file processed")
    input_hash: str = Field(..., description="SHA-256 hash of input file")
    output_parquet: str = Field(..., description="Relative path of generated Parquet file")
    output_hash: str = Field(..., description="SHA-256 hash of generated Parquet file")
    row_count: int = Field(..., ge=0, description="Total valid row count written to Parquet")
    schema_definition: dict[str, str] = Field(default_factory=dict, description="Field name to Arrow/Parquet data type mapping")
    started_at: datetime = Field(..., description="Worker start timestamp")
    completed_at: datetime = Field(..., description="Worker completion timestamp")
    lineage: dict[str, Any] = Field(default_factory=dict, description="Lineage details (input boundaries, processing parameters, steps)")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings recorded during execution")
    quarantined: bool = Field(default=False, description="Flag indicating if job output was quarantined")
    quarantine_reason: str | None = Field(default=None, description="Reason for quarantine if quarantined")
