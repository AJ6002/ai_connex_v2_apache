"""
conftest.py - Global pytest fixtures (G-12 Fix)
=================================================
Provides reusable synthetic DataFrames, manifest templates, and temporary workspace
fixtures across unit, matrix, contract, and scenario tests.
"""

import os
import json
import re
import tempfile
import pytest
import numpy as np
import pandas as pd


@pytest.fixture
def synthetic_tabular_df():
    """Returns a synthetic 100-row tabular regression DataFrame."""
    np.random.seed(42)
    return pd.DataFrame({
        "feature_1": np.random.randn(100),
        "feature_2": np.random.randn(100),
        "feature_3": np.random.randn(100),
        "target": np.random.randn(100) * 10 + 50,
    })


@pytest.fixture
def synthetic_time_series_df():
    """Returns a synthetic 120-row multi-asset time series DataFrame."""
    np.random.seed(42)
    rows = []
    for unit in range(1, 5):  # 4 engines
        for cycle in range(1, 31):
            rows.append({
                "unit": unit,
                "cycle": cycle,
                "s1": np.random.randn(),
                "s2": np.random.randn(),
                "s3": np.random.randn(),
                "RUL": float(100 - cycle),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def sample_manifest(tmp_path):
    """Returns a standard manifest dictionary and saves a temporary JSON copy."""
    manifest = {
        "pipeline_run_id": "test_run_001",
        "ml_task": "regression",
        "data_topology": "multi_entity_time_series",
        "schema_config": {
            "entity_column": "unit",
            "timestamp_column": "cycle",
            "raw_features": ["s1", "s2", "s3"],
        },
        "label_contract": {
            "target_column": "RUL",
            "target_type": "time_to_event",
            "regime": "continuous",
        },
        "features_config": {
            "lag_features": True,
            "spectral_features": False,
            "normalization": "global",
        },
        "hpo_config": {
            "n_iter": 5,
            "scoring": "neg_root_mean_squared_error",
        },
        "candidate_algorithms": ["RandomForest", "LinearRegression"],
        "validation_gates": {
            "vg_1": {"min_train_rows": 10},
            "vg_2": {"r2_min": 0.5, "rmse_threshold": 20.0},
        },
    }
    manifest_file = tmp_path / "test_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    manifest["paths"] = {"manifest_self": str(manifest_file)}
    return manifest


@pytest.fixture(autouse=True)
def _reset_memory_event_store():
    """
    Autouse fixture: resets the process-wide Memory Agent EventStore singleton
    before every test. Without this, any test exercising the full LangGraph
    (which routes through the real event-sourced Memory Agent node) leaks
    events into the shared singleton, silently polluting whatever test runs
    next in the same pytest session (Phase 5a).
    """
    try:
        from aiconnex_agent.memory.event_store import reset_event_store
        reset_event_store()
    except ImportError:
        pass
    yield


@pytest.fixture(autouse=True)
def _reset_semantic_memory_backend():
    """
    Autouse fixture: resets the process-wide SemanticMemoryBackend singleton
    before every test (Phase 5a.6). Same rationale as _reset_memory_event_store -
    any test exercising the real Memory Agent write/read paths mirrors Entity
    memory into this singleton, which would otherwise leak semantic search hits
    across unrelated test files in the same pytest session.
    """
    try:
        from aiconnex_agent.memory.backends.factory import reset_semantic_backend
        reset_semantic_backend()
    except ImportError:
        pass
    yield


class _FakeLLMResponse:
    """Mimics a LangChain AIMessage's .content attribute."""
    def __init__(self, content: str):
        self.content = content


class _FakeSemanticExtractionLLM:
    """
    Deterministic stand-in for the real LLM client (Ollama/OpenAI) used ONLY
    inside SemanticExtractor's _extract_via_llm() during tests. It reuses
    SemanticExtractor's own deterministic heuristic to generate its "response" -
    so the REAL LLM code path (invoke -> parse JSON -> validate -> normalize)
    is genuinely exercised in tests, without any live network call.
    """
    def invoke(self, prompt: str):
        match = re.search(r"User Prompt:\s*(.*)", prompt, re.DOTALL)
        user_prompt = match.group(1).strip() if match else prompt

        from aiconnex_agent.parser.semantic_extractor import SemanticExtractor
        payload = SemanticExtractor(use_llm=False)._extract_heuristic(user_prompt)
        return _FakeLLMResponse(json.dumps(payload))


@pytest.fixture(autouse=True)
def _fake_llm_for_semantic_extractor(monkeypatch):
    """
    Autouse fixture: SemanticExtractor now makes a REAL LLM call by default
    (use_llm=True). This fixture replaces only the network boundary
    (aiconnex_agent.parser.semantic_extractor.get_llm) with a deterministic
    fake so the test suite never depends on a live Ollama/OpenAI connection -
    the extractor's actual call/parse/validate/normalize logic still runs.
    Tests that want to exercise the real network path explicitly construct
    their own SemanticExtractor and monkeypatch get_llm themselves instead.
    """
    try:
        import aiconnex_agent.parser.semantic_extractor as se_module
        monkeypatch.setattr(se_module, "get_llm", lambda *a, **kw: _FakeSemanticExtractionLLM())
    except ImportError:
        pass
    yield


class _FakeConfidenceScorerLLM:
    """
    Deterministic stand-in for the real LLM client used ONLY inside
    ConfidenceScorer's _score_via_llm() during tests. Reuses ConfidenceScorer's
    own rule-based ladder to generate its "response" - so the REAL LLM code
    path (invoke -> parse JSON -> validate range) is genuinely exercised in
    tests, without any live network call.
    """
    def invoke(self, prompt: str):
        match = re.search(r"Primary intent:\s*(\S+)", prompt)
        intent = match.group(1) if match else "general"
        files_match = re.search(r"Mentioned files:\s*(\[.*?\])", prompt)
        has_files = files_match is not None and files_match.group(1) != "[]"

        if intent != "general" and has_files:
            confidence = 0.95
        elif intent != "general":
            confidence = 0.88
        elif has_files:
            confidence = 0.86
        else:
            confidence = 0.50

        return _FakeLLMResponse(json.dumps({"confidence": confidence, "reasoning": "fake test LLM"}))


class _FakeClarificationGeneratorLLM:
    """
    Deterministic stand-in for the real LLM client used ONLY inside
    ClarificationGenerator's _generate_via_llm() during tests. Reuses
    ClarificationGenerator's own template heuristic to generate its
    "response" - so the REAL LLM code path is genuinely exercised in tests,
    without any live network call.
    """
    def invoke(self, prompt: str):
        from aiconnex_agent.schemas import ConversationUnderstandingContract
        from aiconnex_agent.parser.clarification_generator import ClarificationGenerator

        intent_match = re.search(r"Primary intent extracted so far:\s*(\S+)", prompt)
        intent = intent_match.group(1) if intent_match else "general"
        files_match = re.search(r"Mentioned files:\s*(\[.*?\])", prompt)
        has_files = files_match is not None and files_match.group(1) != "[]"

        cuc = ConversationUnderstandingContract(
            goal={"primary_intent": intent},
            observed={"mentioned_files": ["placeholder.zip"] if has_files else []},
        )
        questions = ClarificationGenerator(use_llm=False)._generate_heuristic(cuc)
        return _FakeLLMResponse(json.dumps({"questions": questions}))


@pytest.fixture(autouse=True)
def _fake_llm_for_confidence_scorer(monkeypatch):
    """
    Autouse fixture: ConfidenceScorer now makes a REAL LLM call by default
    (use_llm=True). Replaces only the network boundary
    (aiconnex_agent.parser.confidence_scorer.get_llm) with a deterministic
    fake so tests never depend on a live LLM connection.
    """
    try:
        import aiconnex_agent.parser.confidence_scorer as cs_module
        monkeypatch.setattr(cs_module, "get_llm", lambda *a, **kw: _FakeConfidenceScorerLLM())
    except ImportError:
        pass
    yield


@pytest.fixture(autouse=True)
def _fake_llm_for_clarification_generator(monkeypatch):
    """
    Autouse fixture: ClarificationGenerator now makes a REAL LLM call by
    default (use_llm=True). Replaces only the network boundary
    (aiconnex_agent.parser.clarification_generator.get_llm) with a
    deterministic fake so tests never depend on a live LLM connection.
    """
    try:
        import aiconnex_agent.parser.clarification_generator as cg_module
        monkeypatch.setattr(cg_module, "get_llm", lambda *a, **kw: _FakeClarificationGeneratorLLM())
    except ImportError:
        pass
    yield
