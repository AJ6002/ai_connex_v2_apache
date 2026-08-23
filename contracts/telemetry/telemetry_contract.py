"""
Telemetry Contract - Industrial sensor and telemetry stream contract.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryContract(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor tag ID")
    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    asset_id: str = Field(..., description="Target asset ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float = Field(..., description="Sensor reading numerical value")
    unit: str = Field(..., description="Engineering unit (e.g. °C, PSI, mm/s)")
    quality_flag: str = Field(default="GOOD", description="GOOD, BAD, UNCERTAIN")
