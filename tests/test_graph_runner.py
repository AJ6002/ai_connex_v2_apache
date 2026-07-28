# tests/test_graph_runner.py
import pytest
from aiconnex_agent.runner import execute_and_stream
from aiconnex_agent.state import MasterAgentState


def test_execute_and_stream():
    initial_state = MasterAgentState(messages=[{"role": "user", "content": "compile data"}])
    events = list(execute_and_stream(initial_state, thread_id="runner_thread_1"))
    
    assert len(events) >= 5
    node_names = [e["node"] for e in events if "node" in e]
    assert "conversation_parser_node" in node_names
    assert "scout_agent_node" in node_names
