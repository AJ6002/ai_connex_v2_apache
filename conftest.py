"""
conftest.py - Root pytest configuration
=======================================
Applies to every test directory in the repository.

Disables the LLM-driven intelligence layer for the whole test suite. Without
this, each UnifiedCompiler construction probes the Ollama server and (if one is
running locally) makes real LLM calls, which makes the suite slow and
non-deterministic.

Tests that specifically exercise LLM behaviour should use a mocked LLMClient
rather than re-enabling this.
"""

from __future__ import annotations

import pytest

from aiconnex_zip_compiler.intelligence.llm_client import (
    DISABLE_ENV_VAR,
    reset_availability_cache,
)


@pytest.fixture(autouse=True)
def _disable_llm_for_tests(monkeypatch):
    """Force the intelligence layer into deterministic-only mode for all tests."""
    monkeypatch.setenv(DISABLE_ENV_VAR, "1")
    reset_availability_cache()
    yield
    reset_availability_cache()
