# tests/test_tui_status_inspector.py
import pytest
from rich.console import Console
from rich.panel import Panel
from aiconnex_agent.state import MasterAgentState
from agentic_terminla_UI.components.status_inspector import render_status_inspector


def test_render_status_inspector():
    state = MasterAgentState(active_agent="scout", confidence_score=0.95)
    panel = render_status_inspector(state)
    assert isinstance(panel, Panel)
    
    console = Console(width=100)
    with console.capture() as capture:
        console.print(panel)
    output_text = capture.get()
    assert "SCOUT" in output_text
    assert "95.0%" in output_text
