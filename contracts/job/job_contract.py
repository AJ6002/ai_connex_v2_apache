"""
Job Contract - Pipeline execution job lifecycle and stage status contract.
Reconciled with web/ TypeScript Job entity types.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    AWAITING_CLARIFICATION = "AWAITING_CLARIFICATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobStageStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class JobStageContract(BaseModel):
    key: str = Field(..., description="Stage identifier (e.g. INTAKE, PROFILER, FEATURE_ENG, TRAINING)")
    label: str = Field(..., description="Human readable stage label")
    status: JobStageStatus = Field(default=JobStageStatus.PENDING, description="Stage status")
    detail: str | None = Field(None, description="Optional live detail line")
    progress_pct: float | None = Field(None, description="0-100 progress percentage")


class JobContract(BaseModel):
    job_id: str = Field(..., description="Unique job execution ID (e.g. JOB-8294)")
    tenant_uid: str = Field(..., description="Tenant organization ID")
    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    intent_uid: str = Field(..., description="Associated Intent Envelope ID")
    status: JobStatus = Field(default=JobStatus.QUEUED, description="Job status")
    stages: list[JobStageContract] = Field(default_factory=list, description="Ordered pipeline execution stages")
    artifact_id: str | None = Field(None, description="Output artifact package ID if complete")
    failure_reason: str | None = Field(None, description="Failure detail if status is FAILED")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
