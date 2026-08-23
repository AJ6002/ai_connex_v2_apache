"""
PREPARE Contract - Data cleaning, transformation, and readiness contract.
"""


from pydantic import BaseModel, Field


class PrepareContract(BaseModel):
    manifest_id: str = Field(..., description="Target manifest ID")
    imputation_methods: dict[str, str] = Field(default_factory=dict, description="Null imputation method per column")
    scaling_method: str | None = Field(None, description="Scaler applied (standard, minmax, robust)")
    outlier_handling: str | None = Field(None, description="Outlier treatment (clip, remove, isolation_forest)")
    unit_conversions: dict[str, str] = Field(default_factory=dict, description="Unit normalization mapping")
    status: str = Field(default="PREPARED", description="Status: PREPARED, WARNINGS, FAILED")
