"""
tests/test_agent_chat.py
------------------------
Task 1 tests for POST /api/agent/chat and POST /api/agent/resume.

Pass criteria:
- /api/agent/chat with a message returns an SSE stream that includes a
  "done" event containing a stable session_id.
- A second call with the same session_id continues the same thread
  (session_id echoed back unchanged).
- /api/agent/resume with a bad body returns 400.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app


def _parse_sse(raw: bytes) -> list[dict]:
    """Parse raw SSE bytes into a list of event dicts."""
    events = []
    for line in raw.decode("utf-8").splitlines():
        if line.startswith("data:"):
            payload = line[len("data:"):].strip()
            try:
                events.append(json.loads(payload))
            except json.JSONDecodeError:
                pass
    return events


class TestAgentChatEndpoint:
    def setup_method(self):
        self.client = app.test_client()

    def test_chat_returns_done_with_session_id(self):
        """First turn must produce a done event with a non-empty session_id."""
        res = self.client.post(
            "/api/agent/chat",
            json={"message": "I want to predict machine failures"},
            content_type="application/json",
        )
        assert res.status_code == 200
        assert res.content_type == "text/event-stream"

        events = _parse_sse(res.data)
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(done_events) >= 1, f"Expected at least one 'done' event, got: {events}"
        session_id = done_events[-1].get("session_id", "")
        assert session_id, "done event must carry a non-empty session_id"

    def test_second_turn_preserves_session_id(self):
        """session_id supplied on turn 2 must be echoed back unchanged."""
        # Turn 1
        res1 = self.client.post(
            "/api/agent/chat",
            json={"message": "I want to detect anomalies in turbofan sensor data"},
            content_type="application/json",
        )
        events1 = _parse_sse(res1.data)
        session_id = next(
            (e["session_id"] for e in events1 if e.get("type") == "done"), None
        )
        assert session_id, "Turn 1 must return a session_id"

        # Turn 2 — same thread
        res2 = self.client.post(
            "/api/agent/chat",
            json={"message": "It is a regression task", "session_id": session_id},
            content_type="application/json",
        )
        assert res2.status_code == 200
        events2 = _parse_sse(res2.data)
        done2 = next((e for e in events2 if e.get("type") == "done"), None)
        assert done2 is not None
        assert done2["session_id"] == session_id, (
            f"Expected session_id={session_id}, got {done2['session_id']}"
        )

    def test_missing_message_returns_400(self):
        res = self.client.post(
            "/api/agent/chat",
            json={"session_id": "abc"},
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_resume_missing_body_returns_400(self):
        res = self.client.post(
            "/api/agent/resume",
            json={"session_id": "abc"},  # missing answer
            content_type="application/json",
        )
        assert res.status_code == 400
