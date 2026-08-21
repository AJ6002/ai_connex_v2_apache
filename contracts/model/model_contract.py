"""
Model Contract - ML Studio trained model artifact, evaluation, and ONNX serving contract.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ModelContract(BaseModel):
    model_id: str = Field(..., description="Unique model artifact ID")
    manifest_id: str = Field(..., description="Associated lifecycle manifest ID")
    algorithm_name: str = Field(..., description="Algorithm used (e.g. LightGBM, LSTM, XGBoost)")
    task_type: str = Field(..., description="Regression, Classification, TimeSeries, Anomaly")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Evaluation metrics (RMSE, MAE, R2, F1)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Hyperparameters used")
    onnx_path: Optional[str] = Field(None, description="Exported ONNX model artifact path")
    is_promoted: bool = Field(default=False, description="Promoted for production serving")
    created_at: datetime = Field(default_factory=datetime.utcnow)
