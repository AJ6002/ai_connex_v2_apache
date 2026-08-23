"""
Profile Contract - Data Profiler structural, statistical, and temporal metrics schema.
Includes ProfileSummaryContract DTO composite for Data Studio presentation layer.
"""

from pydantic import BaseModel, Field


class ProfileContract(BaseModel):
    manifest_id: str = Field(..., description="Target manifest ID")
    row_count: int = Field(..., description="Total row count")
    column_count: int = Field(..., description="Total column count")
    columns: list[str] = Field(default_factory=list, description="List of column names")
    numeric_columns: list[str] = Field(default_factory=list, description="List of numeric columns")
    categorical_columns: list[str] = Field(default_factory=list, description="List of categorical columns")
    timestamp_columns: list[str] = Field(default_factory=list, description="List of timestamp columns")
    null_counts: dict[str, int] = Field(default_factory=dict, description="Null count per column")
    null_rates: dict[str, float] = Field(default_factory=dict, description="Null percentage per column")
    stats_summary: dict[str, dict[str, float]] = Field(default_factory=dict, description="Mean, std, min, max per column")
    temporal_range: dict[str, str] = Field(default_factory=dict, description="Start and end timestamps")
    quality_score: float = Field(default=100.0, description="Overall dataset health/quality score (0-100)")


class ColumnSummaryContract(BaseModel):
    name: str = Field(..., description="Column name")
    dtype: str = Field(..., description="Inferred or mapped data type")
    null_ratio: float = Field(default=0.0, description="Null ratio (0.0 - 1.0)")
    distinct_count: int | None = Field(None, description="Distinct value count")


class ProfileSummaryContract(BaseModel):
    manifest_id: str = Field(..., description="Target manifest ID")
    dataset_ref: str = Field(..., description="Associated dataset asset ID or reference")
    dataset_name: str = Field(..., description="Human readable dataset name")
    row_count: int = Field(..., description="Total row count")
    column_count: int = Field(..., description="Total column count")
    columns: list[ColumnSummaryContract] = Field(default_factory=list, description="Detailed column metrics")
    recommended_dag_id: str | None = Field(None, description="Recommended DAG pipeline strategy ID")
    algorithm_family: str | None = Field(None, description="Recommended algorithm family classification")
    narrative: str | None = Field(None, description="AI-generated structural analysis summary")
    quality_score: float = Field(default=100.0, description="Overall health score (0-100)")
