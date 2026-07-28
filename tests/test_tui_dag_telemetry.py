# tests/test_tui_dag_telemetry.py
import pytest
from rich.console import Console
from rich.panel import Panel
from agentic_terminla_UI.components.dag_telemetry import render_telemetry_panel


def test_render_telemetry_panel():
    events = [
        {"node": "conversation_parser_node", "event": "node_update"},
        {"node": "scout_agent_node", "event": "node_update"}
    ]
    panel = render_telemetry_panel(events)
    assert isinstance(panel, Panel)
    
    console = Console(width=100)
    with console.capture() as capture:
        console.print(panel)
    output_text = capture.get()
    assert "scout_agent_node" in output_text
