"""
agentic_terminla_UI/components/dag_telemetry.py
================================================
LangGraph 3-Agent Routing & Telemetry Panel.
"""

from __future__ import annotations
from typing import List, Dict, Any
from rich.panel import Panel
from rich.text import Text


def render_telemetry_panel(events: List[Dict[str, Any]]) -> Panel:
    """Render live telemetry event stream."""
    text = Text()
    if not events:
        text.append("Waiting for graph execution events...\n", style="dim italic")
    else:
        for idx, ev in enumerate(events[-10:], 1):
            node_name = ev.get("node", "unknown")
            text.append(f"[{idx:02d}] ", style="bold dim")
            text.append(f"⚡ Executed Node: ", style="bold yellow")
            text.append(f"{node_name}\n", style="bold green")
            
    return Panel(text, title="[bold yellow]📡 LangGraph Agent Telemetry Stream[/bold yellow]", border_style="yellow")
