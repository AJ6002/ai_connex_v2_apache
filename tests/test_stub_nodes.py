# tests/test_stub_nodes.py
import pytest
from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.nodes.stub_nodes import (
    stub_conversation_parser_node,
    stub_planning_engine_node,
    stub_scout_agent_node,
)


def test_stub_conversation_parser_node():
    state = MasterAgentState(messages=[{"role": "user", "content": "compile data"}])
    res = stub_conversation_parser_node(state)
    assert res["active_agent"] == "planner"
    assert res["confidence_score"] == 0.95
    assert res["cuc"]["goal"]["primary_intent"] == "compile_zip"


def test_stub_planning_engine_node():
    state = MasterAgentState()
    res = stub_planning_engine_node(state)
    assert len(res["plan_steps"]) == 3
    assert res["plan_steps"][0]["target_agent"] == "scout"


def test_stub_scout_agent_node():
    state = MasterAgentState(plan_steps=[{"target_agent": "scout", "step_id": "step_1"}])
    res = stub_scout_agent_node(state)
    assert res["scout_enriched"]["upload"]["status"] == "uploaded"
    assert res["active_agent"] == "evaluator"
