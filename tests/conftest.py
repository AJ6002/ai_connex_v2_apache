"""
Root Pytest Configuration for AI-Connex Apache v2.
"""

import os
import pytest

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set standard test environment variables."""
    monkeypatch.setenv("INTAKE_UPLOAD_DIR", "services/workspace_data/uploads")
    yield
