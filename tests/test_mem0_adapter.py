# tests/test_mem0_adapter.py
"""
Tests for Mem0Backend (Phase 5a.6 Task 4).

These tests require the OPTIONAL `mem0ai` package plus a locally running
Ollama instance with the `nomic-embed-text` and `llama3.1` models pulled.
None of that is installed/available in the default CI/dev environment for
this repo, so this file is EXPECTED TO SKIP via pytest.importorskip -
that is the correct, intended outcome, not a failure. See
docs/superpowers/plans/2026-07-29-phase5a6-mem0-sprint2.md Task 4.
"""
import os
import pytest

mem0 = pytest.importorskip("mem0", reason="mem0ai is an optional dependency - not installed by default")

from aiconnex_agent.memory.backends.mem0_adapter import Mem0Backend, _build_mem0_config


def test_mem0_backend_config_is_fully_local_ollama_and_qdrant():
    config = _build_mem0_config()
    assert config["llm"]["provider"] == "ollama"
    assert config["embedder"]["provider"] == "ollama"
    assert config["vector_store"]["provider"] == "qdrant"
    # Deliberately not the "-cloud" Ollama model - real local inference only.
    assert "cloud" not in config["llm"]["config"]["model"]
    assert config["vector_store"]["config"]["embedding_model_dims"] == 768


def test_mem0_backend_add_and_search_roundtrip():
    """Requires a live local Ollama (llama3.1 + nomic-embed-text pulled)."""
    backend = Mem0Backend()
    backend.add(
        "dataset ds_nasa_fd001: DatasetCompiled {'rows': 26898}",
        {"subject_id": "ds_nasa_fd001", "subject_type": "dataset"},
    )
    results = backend.search("NASA FD001 dataset rows", limit=5)
    assert isinstance(results, list)
    if results:
        assert "text" in results[0]
        assert "score" in results[0]


def test_mem0_backend_without_install_raises_actionable_runtime_error(monkeypatch):
    """Simulates the mem0ai-absent path even when mem0ai IS installed in this env,
    by patching the module-level _Mem0Memory sentinel back to None."""
    import aiconnex_agent.memory.backends.mem0_adapter as adapter_module

    monkeypatch.setattr(adapter_module, "_Mem0Memory", None)
    with pytest.raises(RuntimeError) as excinfo:
        adapter_module.Mem0Backend()
    assert "mem0ai" in str(excinfo.value).lower()
    assert "pip install" in str(excinfo.value).lower()
