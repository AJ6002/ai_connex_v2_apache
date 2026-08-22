"""
Profile Contract - Data Profiler structural, statistical, and temporal metrics schema.
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
