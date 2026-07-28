# tests/test_tui_app.py
import pytest
from agentic_terminla_UI.tui_app import run_tui_session


def test_run_tui_session_headless():
    res_events = run_tui_session(user_prompt="compile suyash2.zip", thread_id="tui_test_thread", live_display=False)
    assert len(res_events) >= 5
    assert any(e.get("node") == "scout_agent_node" for e in res_events)
