"""
Unit tests for strict 2-tier local GGUF client & deterministic heuristic engine.
"""

from aiconnex_agent.local_gguf_client import (
    DeterministicHeuristicEngine,
    LocalGGUFEngine,
)
from contracts.intent.intent_contract import IntentContract


def test_deterministic_heuristic_engine_time_series():
    engine = DeterministicHeuristicEngine()
    intent = engine.parse_intent(
        user_goal="Predict future compressor vibration anomalies for turbine-01",
        tenant_uid="tenant-alpha",
        user_uid="usr-123"
    )
    assert isinstance(intent, IntentContract)
    assert intent.tenant_uid == "tenant-alpha"
    assert intent.intent_type == "time_series_forecast"
    assert intent.requires_model is True
    assert intent.asset_scope == "compressor"


def test_deterministic_heuristic_engine_anomaly_detection():
    engine = DeterministicHeuristicEngine()
    intent = engine.parse_intent(
        user_goal="Detect fault spikes and outlier anomalies in boiler sensor data",
        tenant_uid="tenant-beta",
        user_uid="usr-456"
    )
    assert isinstance(intent, IntentContract)
    assert intent.intent_type == "anomaly_detection"
    assert intent.requires_model is True
    assert intent.asset_scope == "boiler"


def test_local_gguf_engine_fallback():
    # Without local .gguf binary loaded, must fall back cleanly to Tier 2 Deterministic Engine
    engine = LocalGGUFEngine(model_dir="models")
    intent = engine.generate_intent(
        user_goal="Clean and normalize hourly telemetry data",
        tenant_uid="tenant-gamma",
        user_uid="usr-789"
    )
    assert isinstance(intent, IntentContract)
    assert intent.intent_type == "dataset_preparation"
    assert intent.constraints["parsed_by"] == "deterministic_heuristic_engine"
