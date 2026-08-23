"""
Deployment Contract - Production serving deployment policy and endpoint contract.
"""

from pydantic import BaseModel, Field


class DeploymentContract(BaseModel):
    deployment_id: str = Field(..., description="Unique deployment ID")
    model_id: str = Field(..., description="Target model artifact ID")
    tenant_uid: str = Field(..., description="Tenant organization ID")
    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    endpoint_url: str = Field(..., description="Serving API endpoint URL")
    min_replicas: int = Field(default=1)
    max_replicas: int = Field(default=5)
    serving_engine: str = Field(default="ONNXRuntime", description="ONNXRuntime, FastAPI, Triton")
    status: str = Field(default="ACTIVE", description="PENDING, ACTIVE, HEALTHY, DEGRADED, STOPPED, FAILED")
