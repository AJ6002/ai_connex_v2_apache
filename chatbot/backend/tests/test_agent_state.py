"""
tests/test_agent_state.py
-------------------------
Tests for GET /api/agent/state endpoint.

Pass criteria:
- GET /api/agent/state without session_id returns 400.
- GET /api/agent/state with non-existent session_id returns 404.
- GET /api/agent/state for a seeded session returns 200 with full CUC, plan, readiness, and manifest_ready=True.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app


class TestAgentStateEndpoint:
    def setup_method(self):
        self.client = app.test_client()

    def test_state_missing_session_id(self):
        res = self.client.get("/api/agent/state")
        assert res.status_code == 400
        data = res.get_json()
        assert "error" in data

    def test_state_unknown_session_id(self):
        res = self.client.get("/api/agent/state?session_id=non_existent_thread_999999")
        assert res.status_code == 404
        data = res.get_json()
        assert "error" in data

    def test_state_seeded_session(self):
        # 1. Seed a session
        seed_payload = {
            "session_id": "test_state_seeded_123",
            "manifest": {
                "primary_intent": "predict_rul",
                "task_family": "regression",
                "confidence": 0.95,
                "raw_prompt": "Predict remaining useful life for turbofan engine",
            },
        }
        seed_res = self.client.post("/api/agent/seed", json=seed_payload)
        assert seed_res.status_code == 200
        seed_data = seed_res.get_json()
        assert seed_data.get("manifest_accepted") is True

        # 2. Query state via GET /api/agent/state
        state_res = self.client.get("/api/agent/state?session_id=test_state_seeded_123")
        assert state_res.status_code == 200
        state_data = state_res.get_json()

        assert state_data.get("session_id") == "test_state_seeded_123"
        assert state_data.get("manifest_ready") is True

        cuc = state_data.get("cuc")
        assert cuc is not None
        assert cuc.get("goal", {}).get("primary_intent") == "predict_rul"
        assert cuc.get("goal", {}).get("task_family") == "regression"

        readiness = state_data.get("upload_readiness")
        assert readiness is not None
        assert readiness.get("ready") is True
