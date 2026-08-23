"""
Dataset Contract - Immutable raw asset and compiled dataset asset metadata.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DatasetContract(BaseModel):
    asset_id: str = Field(..., description="Unique dataset asset identifier")
    tenant_uid: str = Field(..., description="Owner tenant ID")
    site_uid: str | None = Field(None, description="Industrial site ID")
    asset_name: str = Field(..., description="Original asset/filename")
    storage_uri: str = Field(..., description="Storage URI (e.g. s3://... or file://...)")
    format: str = Field(..., description="Dataset format: csv, parquet, xlsx, json, zip")
    size_bytes: int = Field(..., description="Size in bytes")
    sha256_hash: str = Field(..., description="SHA-256 integrity hash")
    schema_map: dict[str, str] = Field(default_factory=dict, description="Column name to data type map")
    row_count: int | None = Field(None, description="Total row count")
    column_count: int | None = Field(None, description="Total column count")
    status: str = Field(default="RECEIVED", description="Lifecycle status: RECEIVED, QUARANTINED, PARSED, PROMOTED")
    promoted_at: datetime | None = Field(None, description="Timestamp when promoted to production dataset store")
    created_at: datetime = Field(default_factory=datetime.utcnow)
