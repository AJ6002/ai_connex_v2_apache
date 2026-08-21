"""
Intent Envelope Normalizer - Converts user request text and metadata into typed IntentContract.
"""

import uuid
from typing import List, Optional
from contracts.intent.intent_contract import IntentContract
from registries.intent.registry import lookup_intent_policy

def normalize_user_intent(
    user_goal: str,
    tenant_uid: str,
    user_uid: str,
    site_scope: Optional[str] = None,
    asset_scope: Optional[str] = None,
    raw_asset_ids: Optional[List[str]] = None
) -> IntentContract:
    """
    Map natural language user goal to intent category and typed IntentContract.
    """
    goal_lower = user_goal.lower()
    
    # Classify intent type based on goal keywords
    if "predict" in goal_lower or "forecast" in goal_lower or "rul" in goal_lower:
        intent_type = "time_series_forecast"
        requires_model = True
    elif "anomaly" in goal_lower or "outlier" in goal_lower or "fault" in goal_lower:
        intent_type = "anomaly_analysis"
        requires_model = True
    elif "visual" in goal_lower or "plot" in goal_lower or "chart" in goal_lower:
        intent_type = "sensor_visualization"
        requires_model = False
    elif "reprocess" in goal_lower or "batch" in goal_lower:
        intent_type = "historical_sensor_reprocess"
        requires_model = False
    else:
        intent_type = "hourly_sensor_upload"
        requires_model = False

    policy = lookup_intent_policy(intent_type) or {}
    
    return IntentContract(
        intent_uid=f"intent-{uuid.uuid4().hex[:8]}",
        tenant_uid=tenant_uid,
        user_uid=user_uid,
        site_scope=site_scope,
        asset_scope=asset_scope,
        goal=user_goal,
        domain="industrial_telemetry",
        intent_type=intent_type,
        requested_outputs=["parquet", "visualization"] if not requires_model else ["parquet", "model"],
        requires_model=requires_model,
        requires_visualization=True,
        autonomy_requested="HITL",
        source_refs=raw_asset_ids or [],
        policy_ref=policy.get("route_policy")
    )
