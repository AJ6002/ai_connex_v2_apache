"""
Intent Registry Loader - Maps user goals to expected schemas and route policies.
"""

from typing import Any, Dict

INTENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "hourly_sensor_upload": {
        "intent_type": "hourly_sensor_upload",
        "description": "Routine hourly industrial sensor telemetry ingestion",
        "required_fields": ["timestamp", "asset_id", "sensor_reading"],
        "supported_formats": ["csv", "parquet", "zip"],
        "allowed_operations": ["PARSE_ONLY", "COMPILE"],
        "requires_model": False,
        "output_contract": "DatasetContract",
        "route_policy": "DATA_STUDIO"
    },
    "historical_sensor_reprocess": {
        "intent_type": "historical_sensor_reprocess",
        "description": "Batch historical sensor dataset compilation and profiling",
        "required_fields": ["timestamp"],
        "supported_formats": ["parquet", "csv", "zip"],
        "allowed_operations": ["COMPILE", "PROFILE_ONLY"],
        "requires_model": False,
        "output_contract": "ProfileContract",
        "route_policy": "DATA_STUDIO"
    },
    "sensor_visualization": {
        "intent_type": "sensor_visualization",
        "description": "Interactive data exploration and plotting",
        "required_fields": ["timestamp"],
        "supported_formats": ["csv", "parquet"],
        "allowed_operations": ["MATH_ANALYSIS", "PREPARE"],
        "requires_model": False,
        "output_contract": "ProfileContract",
        "route_policy": "DATA_STUDIO"
    },
    "time_series_forecast": {
        "intent_type": "time_series_forecast",
        "description": "Predict future sensor trajectories / remaining useful life",
        "required_fields": ["timestamp", "target_value"],
        "supported_formats": ["csv", "parquet"],
        "allowed_operations": ["ROUTE_TO_ML"],
        "requires_model": True,
        "output_contract": "ModelContract",
        "route_policy": "ML_STUDIO"
    },
    "anomaly_analysis": {
        "intent_type": "anomaly_analysis",
        "description": "Detect structural or statistical operational anomalies",
        "required_fields": ["timestamp", "sensor_value"],
        "supported_formats": ["csv", "parquet"],
        "allowed_operations": ["MATH_ANALYSIS", "ROUTE_TO_ML"],
        "requires_model": True,
        "output_contract": "ModelContract",
        "route_policy": "ML_STUDIO"
    },
    "machine_health_monitoring": {
        "intent_type": "machine_health_monitoring",
        "description": "Continuous vibration and temperature asset health monitoring",
        "required_fields": ["timestamp", "asset_id"],
        "supported_formats": ["csv", "parquet", "zip"],
        "allowed_operations": ["COMPILE_THEN_PROFILE"],
        "requires_model": False,
        "output_contract": "ProfileContract",
        "route_policy": "DATA_STUDIO"
    },
    "NEEDS_CLARIFICATION": {
        "intent_type": "NEEDS_CLARIFICATION",
        "description": "Fallback route for ambiguous user goals requiring clarification",
        "required_fields": [],
        "supported_formats": [],
        "allowed_operations": ["PROMPT_CLARIFICATION"],
        "requires_model": False,
        "output_contract": "IntentContract",
        "route_policy": "AWAITING_CLARIFICATION"
    },
    "BLOCK": {
        "intent_type": "BLOCK",
        "description": "Fallback route for rejected, security-flagged, or unsafe intents",
        "required_fields": [],
        "supported_formats": [],
        "allowed_operations": ["REJECT"],
        "requires_model": False,
        "output_contract": "AuditContract",
        "route_policy": "QUARANTINED"
    }
}


def lookup_intent_policy(intent_type: str) -> Dict[str, Any]:
    """
    Retrieve registered intent policy rules for a given intent type.
    Returns NEEDS_CLARIFICATION policy fallback if intent_type is unknown or unregistered.
    """
    return INTENT_REGISTRY.get(intent_type, INTENT_REGISTRY["NEEDS_CLARIFICATION"])
