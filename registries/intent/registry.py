"""
Intent Registry Loader - Maps user goals to expected schemas and route policies.
"""

from typing import Dict, Any, List, Optional
from contracts.intent.intent_contract import IntentContract

INTENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "hourly_sensor_upload": {
        "intent_type": "hourly_sensor_upload",
        "description": "Routine hourly industrial sensor telemetry ingestion",
        "required_fields": ["timestamp", "asset_id", "sensor_reading"],
        "supported_formats": ["csv", "parquet", "zip"],
        "allowed_operations": ["PARSE_ONLY", "COMPILE"],
        "route_policy": "DATA_STUDIO"
    },
    "historical_sensor_reprocess": {
        "intent_type": "historical_sensor_reprocess",
        "description": "Batch historical sensor dataset compilation and profiling",
        "required_fields": ["timestamp"],
        "supported_formats": ["parquet", "csv", "zip"],
        "allowed_operations": ["COMPILE", "PROFILE_ONLY"],
        "route_policy": "DATA_STUDIO"
    },
    "sensor_visualization": {
        "intent_type": "sensor_visualization",
        "description": "Interactive data exploration and plotting",
        "required_fields": ["timestamp"],
        "supported_formats": ["csv", "parquet"],
        "allowed_operations": ["MATH_ANALYSIS", "PREPARE"],
        "route_policy": "DATA_STUDIO"
    },
    "time_series_forecast": {
        "intent_type": "time_series_forecast",
        "description": "Predict future sensor trajectories / remaining useful life",
        "required_fields": ["timestamp", "target_value"],
        "supported_formats": ["csv", "parquet"],
        "allowed_operations": ["ROUTE_TO_ML"],
        "route_policy": "ML_STUDIO"
    },
    "anomaly_analysis": {
        "intent_type": "anomaly_analysis",
        "description": "Detect structural or statistical operational anomalies",
        "required_fields": ["timestamp", "sensor_value"],
        "supported_formats": ["csv", "parquet"],
        "allowed_operations": ["MATH_ANALYSIS", "ROUTE_TO_ML"],
        "route_policy": "ML_STUDIO"
    },
    "machine_health_monitoring": {
        "intent_type": "machine_health_monitoring",
        "description": "Continuous vibration and temperature asset health monitoring",
        "required_fields": ["timestamp", "asset_id"],
        "supported_formats": ["csv", "parquet", "zip"],
        "allowed_operations": ["COMPILE_THEN_PROFILE"],
        "route_policy": "DATA_STUDIO"
    }
}

def lookup_intent_policy(intent_type: str) -> Optional[Dict[str, Any]]:
    """Retrieve registered intent policy rules for a given intent type."""
    return INTENT_REGISTRY.get(intent_type)
