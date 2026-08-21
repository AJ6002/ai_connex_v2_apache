"""
Feature Contract - Feature engineering and dataset feature set contract.
"""

from typing import List
from pydantic import BaseModel, Field

class FeatureContract(BaseModel):
    feature_set_id: str = Field(..., description="Unique feature set ID")
    manifest_id: str = Field(..., description="Target manifest ID")
    feature_names: List[str] = Field(default_factory=list, description="Names of engineered features")
    time_domain_features: List[str] = Field(default_factory=list, description="Time domain signal features")
    frequency_domain_features: List[str] = Field(default_factory=list, description="FFT / spectral features")
    lag_features: List[str] = Field(default_factory=list, description="Lagged sensor features")
    feature_count: int = Field(default=0, description="Total feature count")
