# tests/test_langgraph_topology.py
import pytest
from aiconnex_agent.graph import build_graph
from aiconnex_agent.state import MasterAgentState


def test_full_graph_execution_happy_path():
    graph = build_graph()
    initial_state = MasterAgentState(messages=[{"role": "user", "content": "compile suyash2.zip"}])
    config = {"configurable": {"thread_id": "test_thread_1"}}
    
    res = graph.invoke(initial_state, config=config)
    assert res["active_agent"] == "complete"
    assert res["current_step_index"] == 3
    assert res["dic"]["compiled_dataset"]["rows"] == 26898


def test_full_graph_execution_ambiguous_hitl_interrupt():
    graph = build_graph()
    initial_state = MasterAgentState(messages=[{"role": "user", "content": "ambiguous prompt"}])
    config = {"configurable": {"thread_id": "test_thread_2"}}
    
    res_interrupt = graph.invoke(initial_state, config=config)
    assert res_interrupt["active_agent"] == "clarification" or "__interrupt__" in res_interrupt
