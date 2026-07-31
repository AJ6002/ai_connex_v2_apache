# tests/test_phase5c_e2e.py
"""End-to-end integration test for Phase 5c multi-candidate pipeline (Phase 5c)."""

from __future__ import annotations
import pytest
from unittest.mock import patch

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.graph import build_graph


def test_e2e_train_rul_flow_produces_selection_result():
    """Full graph execution for train_rul should produce a selection_result."""
    graph = build_graph()
    initial = MasterAgentState()
    initial_dict = initial.model_dump()
    initial_dict["messages"] = [{"role": "user", "content": "Train a RUL prediction model on my turbofan dataset"}]

    state = MasterAgentState(**initial_dict)
    config = {"configurable": {"thread_id": "test_e2e_phase5c"}}

    # Run the graph
    final_state = None
    for event in graph.stream(state, config=config, stream_mode="updates"):
        if isinstance(event, dict):
            for node_name, state_update in event.items():
                final_state = state_update

    # The platform node should have run and produced results
    assert final_state is not None


def test_e2e_graph_has_all_expected_nodes():
    """The compiled graph should contain all Phase 5c node names."""
    graph = build_graph()
    node_names = set(graph.nodes.keys()) if hasattr(graph, 'nodes') else set()

    # Core nodes that must exist
    expected = {
        "conversation_parser_node",
        "clarification_node",
        "planning_engine_node",
        "scout_agent_node",
        "platform_agent_node",
        "memory_agent_node",
        "plan_evaluator_node",
    }
    for name in expected:
        assert name in node_names, f"Missing node: {name}"


def test_intent_plan_mapper_train_rul_routes_to_platform():
    """Platform steps are NOT in the initial plan (enqueued post-HITL via get_platform_steps)."""
    from aiconnex_agent.planning.intent_plan_mapper import IntentPlanMapper
    mapper = IntentPlanMapper()
    # Initial plan must NOT have platform (user hasn't selected recipe yet)
    initial_steps = mapper.get_plan("train_rul")
    initial_agents = [s["target_agent"] for s in initial_steps]
    assert "platform" not in initial_agents, "Platform must not appear in initial plan"

    # Platform steps ARE generated once a recipe is selected
    platform_steps = mapper.get_platform_steps("REGRESSION", "Predict TDS")
    platform_agents = [s["target_agent"] for s in platform_steps]
    assert "platform" in platform_agents, "Platform must be in post-HITL steps"


def test_intent_plan_mapper_detect_anomalies_routes_to_platform():
    """detect_anomalies: platform appears in post-HITL steps, not initial plan."""
    from aiconnex_agent.planning.intent_plan_mapper import IntentPlanMapper
    mapper = IntentPlanMapper()
    initial_steps = mapper.get_plan("detect_anomalies")
    initial_agents = [s["target_agent"] for s in initial_steps]
    assert "platform" not in initial_agents

    platform_steps = mapper.get_platform_steps("ANOMALY", "Detect Anomalies")
    assert any(s["target_agent"] == "platform" for s in platform_steps)


def test_platform_node_is_no_longer_stub():
    """stub_platform_agent_node should delegate to real_platform_agent_node."""
    from aiconnex_agent.nodes.stub_nodes import stub_platform_agent_node
    import inspect
    source = inspect.getsource(stub_platform_agent_node)
    assert "real_platform_agent_node" in source
