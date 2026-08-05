"""
tests/test_upload_bridge.py
---------------------------
Task 4 tests for the upload bridge: /api/upload with session_id resumes
the LangGraph thread into Scout and streams SSE events.

Pass criteria:
- Upload without session_id returns JSON (legacy path unchanged).
- Upload without file returns 400.
- Upload with session_id and file returns text/event-stream with a done event.
"""

import io
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app

TINY_CSV = b"id,value\n1,42\n2,99\n"


def _parse_sse(raw: bytes) -> list[dict]:
    events = []
    for line in raw.decode("utf-8").splitlines():
        if line.startswith("data:"):
            payload = line[len("data:"):].strip()
            try:
                events.append(json.loads(payload))
            except json.JSONDecodeError:
                pass
    return events


class TestUploadBridge:
    def setup_method(self):
        self.client = app.test_client()

    def test_upload_without_file_returns_400(self):
        res = self.client.post("/api/upload", data={"session_id": "abc"})
        assert res.status_code == 400

    def test_upload_without_session_id_returns_json(self):
        """Legacy path: no session_id → JSON response (backward compatibility)."""
        data = {
            "file": (io.BytesIO(TINY_CSV), "test_legacy.csv"),
        }
        res = self.client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert res.status_code == 200
        # Legacy path returns JSON (may take a moment for Scout)
        body = res.get_json()
        assert body is not None
        assert "filename" in body or "reply" in body

    def test_upload_with_session_id_returns_sse(self):
        """SSE path: session_id → text/event-stream with done event."""
        # First get a session_id via chat
        res1 = self.client.post(
            "/api/agent/chat",
            json={"message": "I want to detect anomalies in pump sensor readings"},
            content_type="application/json",
        )
        events1 = _parse_sse(res1.data)
        session_id = next(
            (e["session_id"] for e in events1 if e.get("type") == "done"), None
        )
        assert session_id, "Must get session_id from /chat before upload"

        # Upload with session_id
        data = {
            "file": (io.BytesIO(TINY_CSV), "test_upload_bridge.csv"),
            "session_id": session_id,
        }
        res2 = self.client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert res2.status_code == 200
        assert res2.content_type == "text/event-stream"

        events2 = _parse_sse(res2.data)
        # Must include at least a text + done event
        types = {e.get("type") for e in events2}
        assert "done" in types, f"Expected 'done' event, got: {types}"
        done = next(e for e in events2 if e.get("type") == "done")
        assert "session_id" in done
        assert "compiled_csv_path" in done or "filename" in done
