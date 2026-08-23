"""
Model Contract - ML Studio trained model artifact, evaluation, and ONNX serving contract.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelContract(BaseModel):
    model_id: str = Field(..., description="Unique model artifact ID")
    tenant_uid: str = Field(..., description="Tenant organization ID")
    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    manifest_id: str = Field(..., description="Associated lifecycle manifest ID")
    algorithm_name: str = Field(..., description="Algorithm used (e.g. LightGBM, LSTM, XGBoost)")
    task_type: str = Field(..., description="Regression, Classification, TimeSeries, Anomaly")
    metrics: dict[str, float] = Field(default_factory=dict, description="Evaluation metrics (RMSE, MAE, R2, F1)")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Hyperparameters used")
    onnx_path: str | None = Field(None, description="Exported ONNX model artifact path")
    is_promoted: bool = Field(default=False, description="Promoted for production serving")
    created_at: datetime = Field(default_factory=datetime.utcnow)
