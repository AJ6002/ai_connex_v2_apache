"""
Unit & Integration tests for Jane Copilot LangGraph StateGraph engine.
"""

from aiconnex_agent.jane_copilot import JaneCopilot


def test_jane_copilot_execution_flow():
    copilot = JaneCopilot()
    final_state = copilot.run(
        user_goal="Forecast hourly compressor temperature telemetry for site-42",
        tenant_uid="tenant-prod",
        user_uid="usr-operator-1",
        site_scope="site-42",
        asset_scope="compressor",
        raw_asset_ids=["asset-999"],
        autonomy_requested="AUTO"
    )

    assert final_state["status"] == "QUALITY_VERIFIED"
    assert final_state["intent_contract"] is not None
    assert final_state["intent_contract"].intent_type == "time_series_forecast"
    assert final_state["discovery_artifact"] is not None
    assert final_state["quality_passed"] is True


def test_jane_copilot_hitl_clarification_flag():
    copilot = JaneCopilot()
    final_state = copilot.run(
        user_goal="Check data",  # Ambiguous low confidence goal
        tenant_uid="tenant-test",
        user_uid="usr-operator-2",
        autonomy_requested="HITL"
    )

    assert final_state["requires_hitl"] is True
    assert final_state["confidence_score"] < 0.85
    assert final_state["status"] == "HITL_CHECKED"
