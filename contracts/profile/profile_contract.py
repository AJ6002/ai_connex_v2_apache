"""
Profile Contract - Data Profiler structural, statistical, and temporal metrics schema.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ProfileContract(BaseModel):
    manifest_id: str = Field(..., description="Target manifest ID")
    row_count: int = Field(..., description="Total row count")
    column_count: int = Field(..., description="Total column count")
    columns: List[str] = Field(default_factory=list, description="List of column names")
    numeric_columns: List[str] = Field(default_factory=list, description="List of numeric columns")
    categorical_columns: List[str] = Field(default_factory=list, description="List of categorical columns")
    timestamp_columns: List[str] = Field(default_factory=list, description="List of timestamp columns")
    null_counts: Dict[str, int] = Field(default_factory=dict, description="Null count per column")
    null_rates: Dict[str, float] = Field(default_factory=dict, description="Null percentage per column")
    stats_summary: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Mean, std, min, max per column")
    temporal_range: Dict[str, str] = Field(default_factory=dict, description="Start and end timestamps")
    quality_score: float = Field(default=100.0, description="Overall dataset health/quality score (0-100)")
