"""
agentic_terminla_UI/components/status_inspector.py
===================================================
Status & Contract Inspector Panel inspired by agent-of-empires UX.
"""

from __future__ import annotations
from rich.panel import Panel
from rich.table import Table
from aiconnex_agent.state import MasterAgentState


def render_status_inspector(state: MasterAgentState) -> Panel:
    """Render top header & contract status panel."""
    table = Table.grid(expand=True)
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="bold white")
    
    agent_name = str(state.active_agent or "unknown").upper()
    agent_color = "green" if agent_name != "CLARIFICATION" else "bold yellow"
    
    table.add_row("Active Agent Node: ", f"[{agent_color}]{agent_name}[/{agent_color}]")
    table.add_row("Confidence Score: ", f"{state.confidence_score * 100:.1f}%")
    table.add_row("Current Step Index: ", f"{state.current_step_index}")
    table.add_row("Stage 1 CUC Intent: ", str(state.cuc.goal.get("primary_intent", "N/A")))
    table.add_row("Stage 2 Scout Status: ", str(state.scout_enriched.upload.status))
    table.add_row("Stage 4 & 5 DIC Rows: ", str(state.dic.compiled_dataset.rows))
    
    return Panel(table, title="[bold magenta]📋 AIConnex Contract & Session Inspector[/bold magenta]", border_style="blue")
