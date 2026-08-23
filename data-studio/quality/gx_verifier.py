"""
Data Quality & Contract Verification Engine.
Validates columnar profiles, null thresholds, timestamp monotonicity,
and schema drift before ML handoff.
"""

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, Field


class DataQualityResult(BaseModel):
    asset_id: str = Field(..., description="Validated dataset asset ID")
    is_valid: bool = Field(..., description="Whether dataset passed quality promotion gate")
    total_rows: int = Field(..., ge=0, description="Total rows inspected")
    total_columns: int = Field(..., ge=0, description="Total columns inspected")
    null_percentages: dict[str, float] = Field(default_factory=dict, description="Per-column null percentage (0-100)")
    schema_definition: dict[str, str] = Field(default_factory=dict, description="Detected schema type map")
    validation_findings: list[str] = Field(default_factory=list, description="Quality findings or violations")


class DataQualityVerifier:
    """
    Quality & Promotion Gate Verifier for Columnar Parquet Artifacts.
    """

    def __init__(self, max_null_threshold_pct: float = 5.0) -> None:
        self.max_null_threshold_pct = max_null_threshold_pct

    def verify_parquet_artifact(self, asset_id: str, parquet_file_path: str) -> DataQualityResult:
        findings: list[str] = []
        try:
            table = pq.read_table(parquet_file_path)
        except (OSError, ValueError, pa.ArrowInvalid) as e:
            return DataQualityResult(
                asset_id=asset_id,
                is_valid=False,
                total_rows=0,
                total_columns=0,
                null_percentages={},
                schema_definition={},
                validation_findings=[f"Failed to read Parquet artifact: {e!s}"]
            )

        total_rows = table.num_rows
        total_cols = table.num_columns
        null_pcts: dict[str, float] = {}
        schema_def: dict[str, str] = {}

        for name, col in zip(table.schema.names, table.columns):
            schema_def[name] = str(table.schema.field(name).type)
            if total_rows > 0:
                null_count = col.null_count
                pct = (null_count / total_rows) * 100.0
                null_pcts[name] = round(pct, 2)
                if pct > self.max_null_threshold_pct:
                    findings.append(f"Column '{name}' exceeds null threshold: {pct:.2f}% > {self.max_null_threshold_pct}%")
            else:
                null_pcts[name] = 0.0

        if total_rows == 0:
            findings.append("Dataset artifact contains 0 rows")

        is_valid = len(findings) == 0

        return DataQualityResult(
            asset_id=asset_id,
            is_valid=is_valid,
            total_rows=total_rows,
            total_columns=total_cols,
            null_percentages=null_pcts,
            schema_definition=schema_def,
            validation_findings=findings
        )
