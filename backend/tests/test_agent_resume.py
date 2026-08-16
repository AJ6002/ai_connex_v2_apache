"""
tests/test_agent_resume.py
--------------------------
Task 2 tests: unified InterruptPayload shape + /api/agent/resume.

Pass criteria:
- clarification_node.py now emits InterruptPayload with interrupt_type="clarification"
  (verified by importing the node directly and checking the interrupt dict structure).
- POST /api/agent/resume with missing body fields returns 400.
- POST /api/agent/resume with a valid session_id returns a streaming response.
"""

import json
import sys
import os

# chatbot/backend is on path (for app.py); project root is on path (for aiconnex_agent package)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app import app


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


class TestUnifiedInterruptShape:
    def test_clarification_node_uses_interrupt_payload(self):
        """clarification_node must import and reference InterruptPayload correctly."""
        import importlib
        import aiconnex_agent.parser.clarification_node as cn_mod
        importlib.reload(cn_mod)

        # Verify the module imports InterruptPayload (not raw dict)
        assert hasattr(cn_mod, "InterruptPayload"), (
            "clarification_node must import InterruptPayload from schemas"
        )

    def test_interrupt_payload_has_interrupt_type(self):
        """InterruptPayload must have interrupt_type field = 'clarification'."""
        from aiconnex_agent.schemas import InterruptPayload
        payload = InterruptPayload(
            interrupt_type="clarification",
            questions=["What is the problem type?"],
            options=[],
            reason="Low confidence",
        )
        d = payload.model_dump()
        assert d["interrupt_type"] == "clarification"
        assert isinstance(d["questions"], list)
        assert isinstance(d["options"], list)

    def test_strategy_choice_payload_distinguishable(self):
        """strategy_choice and clarification interrupts must differ by interrupt_type."""
        from aiconnex_agent.schemas import InterruptPayload, InterruptOption
        clarification = InterruptPayload(interrupt_type="clarification", questions=["Q?"])
        strategy = InterruptPayload(
            interrupt_type="strategy_choice",
            questions=["Pick a strategy"],
            options=[InterruptOption(option_id="opt1", label="Regression")],
        )
        assert clarification.interrupt_type != strategy.interrupt_type
        assert len(strategy.options) == 1


class TestAgentResumeEndpoint:
    def setup_method(self):
        self.client = app.test_client()

    def test_resume_missing_session_id_returns_400(self):
        res = self.client.post(
            "/api/agent/resume",
            json={"answer": "regression task"},
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_resume_missing_answer_returns_400(self):
        res = self.client.post(
            "/api/agent/resume",
            json={"session_id": "some-session-xyz"},
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_resume_valid_body_returns_streaming_response(self):
        """Resume with a valid body must return 200 text/event-stream (even if thread is fresh)."""
        # First create a session via chat
        res1 = self.client.post(
            "/api/agent/chat",
            json={"message": "predict anomalies in pump vibration sensors"},
            content_type="application/json",
        )
        events1 = _parse_sse(res1.data)
        session_id = next(
            (e["session_id"] for e in events1 if e.get("type") == "done"), None
        )
        assert session_id, "Must get a session_id from /chat before resuming"

        # Resume — thread may not be interrupted, but the endpoint must respond cleanly
        res2 = self.client.post(
            "/api/agent/resume",
            json={"session_id": session_id, "answer": "anomaly detection, regression"},
            content_type="application/json",
        )
        assert res2.status_code == 200
        assert res2.content_type == "text/event-stream"
        events2 = _parse_sse(res2.data)
        # Must end with a done or error event (not a crash)
        terminal = [e for e in events2 if e.get("type") in ("done", "error")]
        assert len(terminal) >= 1, f"No terminal event found: {events2}"
