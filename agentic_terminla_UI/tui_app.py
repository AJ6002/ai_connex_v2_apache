"""
agentic_terminla_UI/tui_app.py - Main Rich Terminal Dashboard App
===================================================================
Connects status_inspector and dag_telemetry to execute_and_stream() from
aiconnex_agent.runner.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in sys.path when running tui_app.py directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.runner import execute_and_stream, resume_with_user_input
from agentic_terminla_UI.components.status_inspector import render_status_inspector
from agentic_terminla_UI.components.dag_telemetry import render_telemetry_panel

console = Console()


def make_layout(state: MasterAgentState, events: List[Dict[str, Any]]) -> Layout:
    """Combine components into a multi-pane layout."""
    layout = Layout()
    layout.split_column(
        Layout(render_status_inspector(state), name="top", size=10),
        Layout(render_telemetry_panel(events), name="bottom"),
    )
    return layout


def run_tui_session(
    user_prompt: str,
    thread_id: str = "tui_session_1",
    live_display: bool = True,
    upload_path: str | None = None,
) -> List[Dict[str, Any]]:
    """Run execution stream with live Rich TUI display.

    upload_path: real filesystem path to the dataset file/archive being
    discussed, if any (Phase 5b gap 1).
    """
    initial_state = MasterAgentState(messages=[{"role": "user", "content": user_prompt}], upload_path=upload_path)
    collected_events = []
    current_state = initial_state
    
    if live_display:
        with Live(make_layout(current_state, collected_events), console=console, refresh_per_second=4) as live:
            for event in execute_and_stream(initial_state, thread_id=thread_id):
                collected_events.append(event)
                state_update = event.get("state_update", {})
                if isinstance(state_update, dict):
                    if "active_agent" in state_update:
                        current_state.active_agent = state_update["active_agent"]
                    if "confidence_score" in state_update:
                        current_state.confidence_score = state_update["confidence_score"]
                    if "current_step_index" in state_update:
                        current_state.current_step_index = state_update["current_step_index"]
                
                live.update(make_layout(current_state, collected_events))
                time.sleep(0.05)
    else:
        for event in execute_and_stream(initial_state, thread_id=thread_id):
            collected_events.append(event)
            state_update = event.get("state_update", {})
            if isinstance(state_update, dict):
                if "active_agent" in state_update:
                    current_state.active_agent = state_update["active_agent"]
                if "confidence_score" in state_update:
                    current_state.confidence_score = state_update["confidence_score"]
                if "current_step_index" in state_update:
                    current_state.current_step_index = state_update["current_step_index"]

    return collected_events


def run_interactive_tui_chat() -> None:
    """Run an interactive live chatbot terminal session with HITL interrupt handling."""
    console.print("\n[bold cyan]=======================================================[/bold cyan]")
    console.print("[bold cyan]🤖 Welcome to AIConnex Master Agent Interactive Chatbot![/bold cyan]")
    console.print("[dim]Type your message or dataset filepath below. Type 'exit' or 'quit' to end.[/dim]")
    console.print("[bold cyan]=======================================================[/bold cyan]\n")

    thread_id = f"chat_{int(time.time())}"
    
    while True:
        try:
            user_input = console.input("\n[bold green]💬 You:[/bold green] ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                console.print("[bold yellow]Ending session. Goodbye![/bold yellow]")
                break
            
            upload_path = None
            if os.path.exists(user_input):
                upload_path = user_input
                user_input = console.input("[bold green]💬 Goal/Query for this dataset file:[/bold green] ").strip()

            events = run_tui_session(user_input, thread_id=thread_id, live_display=True, upload_path=upload_path)
            
            # Retrieve latest state from graph to display Agent response / questions
            from aiconnex_agent.runner import _compiled_graph
            config = {"configurable": {"thread_id": thread_id}}
            snapshot = _compiled_graph.get_state(config)
            state_data = snapshot.values if hasattr(snapshot, "values") else {}

            # Print Assistant response or Clarification questions
            cuc = state_data.get("cuc")
            questions = cuc.clarification_questions if hasattr(cuc, "clarification_questions") and cuc.clarification_questions else []
            
            if questions:
                console.print("\n[bold cyan]🤖 AIConnex Agent:[/bold cyan]")
                for q in questions:
                    console.print(f"  👉 [bold yellow]{q}[/bold yellow]")
            elif state_data.get("selection_result"):
                winner = state_data["selection_result"].get("winning_candidate", {})
                console.print(f"\n[bold cyan]🤖 AIConnex Agent:[/bold cyan] [bold green]ML Pipeline Complete! Winner candidate model: {winner.get('recipe_id')} (Test Score: {winner.get('test_score')})[/bold green]")

            # Check if execution paused on HITL interrupt node
            if snapshot.next and "__interrupt__" in str(snapshot.next):
                resume_input = console.input("\n[bold magenta]👉 Answer:[/bold magenta] ").strip()
                if resume_input:
                    with Live(make_layout(MasterAgentState(), events), console=console, refresh_per_second=4) as live:
                        for event in resume_with_user_input(resume_input, thread_id=thread_id):
                            events.append(event)
                            live.update(make_layout(MasterAgentState(), events))
                            time.sleep(0.05)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Session interrupted. Exiting...[/bold yellow]")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--chat", "-c", "chat"):
            run_interactive_tui_chat()
        else:
            prompt = " ".join(sys.argv[1:])
            run_tui_session(prompt)
    else:
        run_interactive_tui_chat()
