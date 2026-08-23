"""
Intent Contract - Immutable intent envelope for dynamic agent routing and plan proposal.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IntentContract(BaseModel):
    intent_uid: str = Field(..., description="Unique immutable identifier for this intent")
    tenant_uid: str = Field(..., description="Authenticated tenant ID")
    user_uid: str = Field(..., description="Authenticated user ID")
    site_scope: str | None = Field(None, description="Industrial site/facility identifier")
    asset_scope: str | None = Field(None, description="Industrial asset scope (e.g. compressor, turbine)")
    goal: str = Field(..., description="Primary objective or goal expressed by user")
    domain: str = Field(default="industrial_telemetry", description="Industrial domain classification")
    intent_type: str = Field(..., description="Mapped intent class (e.g. hourly_sensor_upload, time_series_forecast)")
    requested_outputs: list[str] = Field(default_factory=list, description="Requested output types (parquet, visualization, model)")
    requires_model: bool = Field(default=False, description="Whether intent requires ML Studio route")
    requires_visualization: bool = Field(default=True, description="Whether intent requires data visualization")
    requires_service: bool = Field(default=False, description="Whether intent requires API data service")
    autonomy_requested: str = Field(default="HITL", description="Autonomy level: HITL, AUTO, CONFIRMATION_ONLY")
    constraints: dict[str, Any] = Field(default_factory=dict, description="Constraints (e.g. max_rows, unit_system)")
    source_refs: list[str] = Field(default_factory=list, description="Source URIs or raw asset IDs")
    policy_ref: str | None = Field(None, description="Security policy ID applied")
    created_at: datetime = Field(default_factory=datetime.utcnow)
