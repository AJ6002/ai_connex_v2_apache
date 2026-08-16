"""
conftest.py - Root pytest configuration
=======================================
Applies to every test directory in the repository.
Disables the LLM-driven intelligence layer for the whole test suite when present.
"""

from __future__ import annotations

import pytest

try:
    from aiconnex_zip_compiler.intelligence.llm_client import (
        DISABLE_ENV_VAR,
        reset_availability_cache,
    )
    HAS_LLM_CLIENT = True
except ImportError:
    HAS_LLM_CLIENT = False


@pytest.fixture(autouse=True)
def _disable_llm_for_tests(monkeypatch):
    """Force the intelligence layer into deterministic-only mode for all tests when available."""
    if HAS_LLM_CLIENT:
        monkeypatch.setenv(DISABLE_ENV_VAR, "1")
        reset_availability_cache()
        yield
        reset_availability_cache()
    else:
        yield
