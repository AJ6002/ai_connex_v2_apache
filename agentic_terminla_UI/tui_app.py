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
    discussed, if any (Phase 5b gap 1) - without it, the real Scout Agent
    node will correctly raise a clarification interrupt instead of
    fabricating fake dataset info.
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


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Compile and profile suyash2.zip archive"
    run_tui_session(prompt)
