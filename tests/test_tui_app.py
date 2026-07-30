# tests/test_tui_app.py
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pytest
from agentic_terminla_UI.tui_app import run_tui_session


@pytest.fixture(autouse=True)
def _cleanup_scout_output():
    yield
    shutil.rmtree(Path("scratch") / "scout_output", ignore_errors=True)


def test_run_tui_session_headless(tmp_path):
    # A real upload_path is required so Scout (Phase 5b) can genuinely compile
    # instead of correctly flagging a missing-file clarification interrupt.
    df = pd.DataFrame({"timestamp": ["2026-01-01 00:00:00"], "value": [1.0]})
    zip_path = tmp_path / "tui_test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data.csv", df.to_csv(index=False))

    res_events = run_tui_session(
        user_prompt="compile suyash2.zip",
        thread_id="tui_test_thread",
        live_display=False,
        upload_path=str(zip_path),
    )
    assert len(res_events) >= 5
    assert any(e.get("node") == "scout_agent_node" for e in res_events)
