# tests/test_langgraph_topology.py
import zipfile
import pandas as pd
import pytest
from aiconnex_agent.graph import build_graph
from aiconnex_agent.state import MasterAgentState


@pytest.fixture
def synthetic_upload_zip(tmp_path):
    """A real, single-table zip - only 1 IntentClassifier option, so Scout
    proceeds through the real UnifiedCompiler without needing a strategy
    clarification interrupt (Gap 7 does not fire for a plain single table)."""
    df = pd.DataFrame({"timestamp": ["2026-01-01 00:00:00", "2026-01-01 00:01:00"], "value": [1.0, 2.0]})
    zip_path = tmp_path / "topology_test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data.csv", df.to_csv(index=False))
    return str(zip_path)


def test_full_graph_execution_happy_path(synthetic_upload_zip):
    # A train_rul intent produces the full 3-step scout -> platform -> memory plan,
    # exercising every agent node and driving current_step_index to 3.
    graph = build_graph()
    initial_state = MasterAgentState(
        messages=[{"role": "user", "content": "train RUL regression model on NASA FD001"}],
        upload_path=synthetic_upload_zip,
    )
    config = {"configurable": {"thread_id": "test_thread_1"}}

    res = graph.invoke(initial_state, config=config)
    assert res["active_agent"] == "complete"
    assert res["current_step_index"] == 3
    # NOTE: not asserting dic.compiled_dataset.rows here - stub_platform_agent_node
    # (Phase 5c, not yet built) still unconditionally overwrites it with a fake
    # hardcoded value after Scout runs. Scout's own real-row-count behavior is
    # verified below in test_full_graph_execution_compile_zip_two_step_plan,
    # whose 2-step plan never reaches the platform node.


def test_full_graph_execution_compile_zip_two_step_plan(synthetic_upload_zip):
    # A compile_zip intent produces a lighter 2-step scout -> memory plan (no platform).
    graph = build_graph()
    initial_state = MasterAgentState(
        messages=[{"role": "user", "content": "compile suyash2.zip"}],
        upload_path=synthetic_upload_zip,
    )
    config = {"configurable": {"thread_id": "test_thread_compile"}}

    res = graph.invoke(initial_state, config=config)
    assert res["active_agent"] == "complete"
    assert res["current_step_index"] == 2
    plan_agents = [s["target_agent"] for s in res["plan_steps"]]
    assert plan_agents == ["scout", "memory"]
    # This plan never reaches the still-fake stub_platform_agent_node, so this
    # genuinely verifies Scout's real UnifiedCompiler row count end-to-end.
    assert res["dic"]["compiled_dataset"]["rows"] == 2


def test_full_graph_execution_ambiguous_hitl_interrupt():
    graph = build_graph()
    initial_state = MasterAgentState(messages=[{"role": "user", "content": "ambiguous prompt"}])
    config = {"configurable": {"thread_id": "test_thread_2"}}
    
    res_interrupt = graph.invoke(initial_state, config=config)
    assert res_interrupt["active_agent"] == "clarification" or "__interrupt__" in res_interrupt
