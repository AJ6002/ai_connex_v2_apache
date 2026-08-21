"""
Manifest Contract - Universal lifecycle join key linking Data Studio, ML Studio, and Agentic Studio.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ManifestContract(BaseModel):
    manifest_id: str = Field(..., description="Universal lifecycle join key (UUID)")
    tenant_uid: str = Field(..., description="Tenant organization ID")
    intent_uid: str = Field(..., description="Associated Intent Envelope ID")
    run_id: str = Field(..., description="Execution run directory ID")
    status: str = Field(default="MACHINE_READY", description="Lifecycle status: MACHINE_READY, READY_FOR_PROFILER, COMPILED, TRAINED, DEPLOYED")
    compiled_parquet_path: Optional[str] = Field(None, description="Canonical compiled Parquet file path")
    schema_map: Dict[str, str] = Field(default_factory=dict, description="Unified schema mapping")
    source_asset_ids: List[str] = Field(default_factory=list, description="Source dataset asset IDs")
    quality_summary_path: Optional[str] = Field(None, description="Great Expectations / Profiler quality report path")
    lineage_path: Optional[str] = Field(None, description="Data lineage JSON path")
    recipe_id: Optional[str] = Field(None, description="Recipe Orchestrator recipe ID")
    model_id: Optional[str] = Field(None, description="ML Studio trained model ID if applicable")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
