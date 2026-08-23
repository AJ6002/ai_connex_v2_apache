"""
Unit tests for Task 1.2.1 Intent Registry validation and fallback routing.
"""

from registries.intent.registry import INTENT_REGISTRY, lookup_intent_policy


def test_intent_registry_fields_completeness():
    """Verify all entries in INTENT_REGISTRY contain required_fields, output_contract, and requires_model."""
    for intent_type, policy in INTENT_REGISTRY.items():
        assert "required_fields" in policy, f"Missing required_fields in {intent_type}"
        assert "output_contract" in policy, f"Missing output_contract in {intent_type}"
        assert "requires_model" in policy, f"Missing requires_model in {intent_type}"
        assert isinstance(policy["requires_model"], bool), f"requires_model is not bool in {intent_type}"


def test_lookup_intent_policy_valid():
    """Verify lookup_intent_policy returns expected policy dict for registered intents."""
    policy = lookup_intent_policy("time_series_forecast")
    assert policy["intent_type"] == "time_series_forecast"
    assert policy["requires_model"] is True
    assert policy["route_policy"] == "ML_STUDIO"
    assert policy["output_contract"] == "ModelContract"


def test_lookup_intent_policy_fallback_needs_clarification():
    """Verify Task 1.2.1 requirement: Unknown/ambiguous intent string returns NEEDS_CLARIFICATION fallback."""
    policy = lookup_intent_policy("invalid_random_user_query_12345")
    assert policy is not None
    assert policy["intent_type"] == "NEEDS_CLARIFICATION"
    assert policy["route_policy"] == "AWAITING_CLARIFICATION"
    assert policy["requires_model"] is False


def test_lookup_intent_policy_fallback_block():
    """Verify BLOCK fallback route is explicitly accessible and defined."""
    policy = lookup_intent_policy("BLOCK")
    assert policy is not None
    assert policy["intent_type"] == "BLOCK"
    assert policy["route_policy"] == "QUARANTINED"
