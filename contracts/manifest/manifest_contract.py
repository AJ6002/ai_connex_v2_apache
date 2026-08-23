"""
Manifest Contract - Universal lifecycle join key linking Data Studio, ML Studio, and Agentic Studio.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ManifestContract(BaseModel):
    manifest_id: str = Field(..., description="Universal lifecycle join key (UUID)")
    tenant_uid: str = Field(..., description="Tenant organization ID")
    intent_uid: str = Field(..., description="Associated Intent Envelope ID")
    run_id: str = Field(..., description="Execution run directory ID")
    status: str = Field(default="MACHINE_READY", description="Lifecycle status: MACHINE_READY, READY_FOR_PROFILER, COMPILED, FEATURES_READY, TRAINED, EVALUATED, DEPLOYED")
    compiled_parquet_path: str | None = Field(None, description="Canonical compiled Parquet file path")
    schema_map: dict[str, str] = Field(default_factory=dict, description="Unified schema mapping")
    source_asset_ids: list[str] = Field(default_factory=list, description="Source dataset asset IDs")
    quality_summary_path: str | None = Field(None, description="Great Expectations / Profiler quality report path")
    lineage_path: str | None = Field(None, description="Data lineage JSON path")
    profile_id: str | None = Field(None, description="Data Profiler summary ID")
    dag_id: str | None = Field(None, description="Associated DAG strategy ID")
    recipe_id: str | None = Field(None, description="Recipe Orchestrator recipe ID")
    feature_set_id: str | None = Field(None, description="Associated feature set ID")
    model_id: str | None = Field(None, description="ML Studio trained model ID if applicable")
    agent_id: str | None = Field(None, description="Associated agent SPEC ID if applicable")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
