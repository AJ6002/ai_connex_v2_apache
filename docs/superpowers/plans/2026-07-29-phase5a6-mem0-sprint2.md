# Phase 5a.6: mem0 Semantic Index Behind Entity Memory (Sprint 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add mem0 as a fuzzy semantic search index sitting BEHIND the Entity memory layer only (per the design guardrail set in the Phase 5a Sprint 1 plan). Decision memory and Procedural memory stay 100% deterministic - mem0 never touches them. This is the project's first memory-related LLM+network dependency; it is gated behind an adapter interface with a deterministic local fake so every existing test keeps running offline.

**Precondition:** Phase 5a Sprint 1 (5a.1-5a.5) is merged and green (78/78 tests passing as of commit fa77159). Do not start this until Sprint 1 is confirmed stable.

## External Prerequisite Research (done - see below for findings)

No mem0 cloud account is required. Two real external dependencies are introduced by this task:

1. **`mem0ai` Python package** (pip install). Base dependency of `mem0ai` includes `openai>=1.90.0` even when OpenAI is never called - this is just an install-time cost, not an account requirement.
2. **Qdrant vector store**. mem0's default is an embedded, on-disk Qdrant instance requiring zero setup (`path`-based, e.g. `/tmp/qdrant` or a repo-local path). A proper Docker-based Qdrant server (port 6333) is only needed if/when this graduates beyond local dev.

**Decision: fully-local mode.** This repo already runs Ollama locally for the main agent LLM (`aiconnex_agent/llm.py`, default `OLLAMA_BASE_URL=http://localhost:11434`). mem0 will reuse that same Ollama instance for both its extraction LLM and its embedder, and use an embedded on-disk Qdrant. This means:
- NO `OPENAI_API_KEY` required.
- NO mem0 cloud account/API key required (that's the separate `app.mem0.ai` SaaS platform - explicitly NOT used here).
- The only new local runtime dependency is Qdrant's embedded on-disk mode, which needs no server process for dev/test.

**Known gotchas to design around:**
- mem0 ships PostHog telemetry ON by default. Must be explicitly disabled (`MEM0_TELEMETRY=false` and, per a known open mem0 issue #3762, an additional guard since the env var alone doesn't always fully suppress background thread creation in some environments). We add a defensive wrapper regardless.
- Embedder output dimension must match the Qdrant collection's configured dimension. `nomic-embed-text` (the Ollama embedding model used in mem0's own Ollama cookbook) is 768-dim - the Qdrant config must set `embedding_model_dims: 768` to match, or mem0 raises a dimension mismatch error.
- `mem0ai` is a real, sizeable dependency footprint (sqlalchemy, posthog, qdrant-client, protobuf, httpx) - not a thin client. This is why it stays behind an adapter interface and is never imported unless `AICONNEX_MEMORY_BACKEND=mem0` is explicitly set.

Sources: [mem0 OSS configuration docs](https://docs.mem0.ai/open-source/configuration), [mem0 Ollama self-hosted cookbook](https://docs.mem0.ai/examples/mem0-with-ollama), [mem0ai pyproject.toml v2.0.14](https://github.com/mem0ai/mem0/blob/main/pyproject.toml), [mem0 telemetry thread-exhaustion issue #3762](https://github.com/mem0ai/mem0/issues/3762).

## Architecture

New sub-package `aiconnex_agent/memory/backends/`:

| Module | Responsibility | LLM/Network |
|---|---|---|
| `base.py` | `SemanticMemoryBackend` interface: `add(text, metadata) -> None`, `search(query, limit) -> List[Dict]` | none |
| `local_fake.py` | In-memory keyword/substring-overlap ranking implementing the interface. Default backend. Used by every existing test. | none |
| `mem0_adapter.py` | Wraps `mem0.Memory` configured for Ollama LLM + Ollama embedder + embedded on-disk Qdrant. Guarded import - module import must not fail if `mem0ai` isn't installed. | LLM (Ollama) + local Qdrant |
| `factory.py` | `get_semantic_backend()` - reads `AICONNEX_MEMORY_BACKEND` env (`local_fake` default, `mem0` opt-in) and returns the configured backend singleton. Mirrors the `AICONNEX_LLM_BACKEND` switch pattern already planned for `llm.py`. | none |

**Integration points (both existing modules, both behind the interface - never a direct mem0 import):**
- `memory_builder.py`: after routing an event into `EntityMemory`, additionally calls `backend.add(...)` with a text summary of the observation + `{subject_id, subject_type}` metadata. Decision and Procedural routing paths are UNCHANGED - they never call the backend.
- `memory_agent.py`: on the `query_status` read path, after building the deterministic `MemoryBank`, additionally calls `backend.search(user_prompt, limit=5)` for fuzzy cross-session recall and merges hits into `memory_context["semantic_hits"]` (a new, clearly-separated key - never merged into `memory_bank` itself, preserving the deterministic/fuzzy separation).

## Global Constraints
- `local_fake` remains the default backend. Installing `mem0ai` is optional; its absence must never break any existing test.
- `mem0_adapter.py` uses a guarded top-level import (`try/except ImportError`) so `aiconnex_agent.memory.backends.mem0_adapter` is importable (and its class definable) even without `mem0ai` installed - the ImportError only surfaces when someone actually tries to instantiate/use it without the package present.
- mem0 sits behind Entity memory ONLY. `DecisionMemory` and `ProceduralMemory` routing in `memory_builder.py` must not change.
- No live mem0/Qdrant process is ever started in the test suite. All mem0-backend tests that need to prove real integration are marked and skipped unless `mem0ai` is actually installed (`pytest.importorskip("mem0")`); the CI/default test run exercises `local_fake` only.
- Telemetry is disabled explicitly (`os.environ.setdefault("MEM0_TELEMETRY", "false")`) inside `mem0_adapter.py` before any mem0 import, as defense-in-depth given the known #3762 issue.

---

### Task 1: SemanticMemoryBackend Interface + LocalFakeBackend

**Files:**
- Create: `aiconnex_agent/memory/backends/__init__.py`
- Create: `aiconnex_agent/memory/backends/base.py`
- Create: `aiconnex_agent/memory/backends/local_fake.py`
- Create: `aiconnex_agent/memory/backends/factory.py`
- Test: `tests/test_memory_semantic_backend.py`

**Interfaces:**
- `SemanticMemoryBackend` (ABC): `add(text: str, metadata: Dict[str, Any]) -> None`, `search(query: str, limit: int = 5) -> List[Dict[str, Any]]` (each result: `{"text": str, "metadata": dict, "score": float}`).
- `LocalFakeBackend`: keyword-overlap scoring (token intersection ratio between query and stored text) - zero LLM, zero network, deterministic ranking.
- `get_semantic_backend() -> SemanticMemoryBackend`: reads `AICONNEX_MEMORY_BACKEND` (default `"local_fake"`); returns a module-level singleton; `reset_semantic_backend()` for test isolation, matching the `EventStore` singleton pattern from 5a.1.

- [ ] Step 1: Write the failing test - add 3 texts about different datasets to `LocalFakeBackend`, search a query matching one -> assert it ranks first with score > 0; assert `get_semantic_backend()` returns `LocalFakeBackend` by default; assert `AICONNEX_MEMORY_BACKEND=mem0` + `mem0ai` NOT installed raises a clear, actionable error (not a cryptic ImportError) when actually used.
- [ ] Step 2: Run test to verify it fails.
- [ ] Step 3: Write minimal implementation of the 4 files above.
- [ ] Step 4: Run test to verify it passes.
- [ ] Step 5: Commit - `git commit -m "feat(memory): SemanticMemoryBackend interface + LocalFakeBackend (Phase 5a.6 Task 1)"`

---

### Task 2: Wire LocalFakeBackend into MemoryBuilder (Entity layer mirroring)

**Files:**
- Modify: `aiconnex_agent/memory/memory_builder.py`
- Test: `tests/test_memory_builder.py` (extend)

**Behavior:** `MemoryBuilder.__init__` accepts an optional `semantic_backend: Optional[SemanticMemoryBackend] = None` (defaults to `get_semantic_backend()`). In `_route_entity`, after appending the observation, call `self.semantic_backend.add(text=<summary>, metadata={"subject_id": ..., "subject_type": ...})`. `_route_decision` and `_route_procedural` are NOT modified - explicit isolation test proves this.

- [ ] Step 1: Write the failing test - build a log with one `DatasetCompiled` + one `ClarificationAnswered` + one failure event through a `MemoryBuilder` wired to a spy/fake backend; assert the backend received exactly 1 `add()` call (from the entity event only); assert decisions/procedures produced no backend calls.
- [ ] Step 2: Run test to verify it fails.
- [ ] Step 3: Implement the wiring.
- [ ] Step 4: Run test to verify it passes + full existing `test_memory_builder.py` suite stays green (idempotency test must still pass - calling `add()` twice on identical input is fine since `LocalFakeBackend.add` is not required to dedupe, but note this explicitly if it affects idempotency assertions).
- [ ] Step 5: Commit - `git commit -m "feat(memory): mirror Entity memory into semantic backend on write path (Phase 5a.6 Task 2)"`

---

### Task 3: Wire semantic search into Memory Agent read path

**Files:**
- Modify: `aiconnex_agent/memory/memory_agent.py`
- Test: `tests/test_memory_agent_node.py` (extend)

**Behavior:** In the `query_status` read path (only), after building the `MemoryBank`, call `backend.search(user_prompt_text, limit=5)` and set `memory_context["semantic_hits"] = [...]`. `memory_context["memory_bank"]` is unchanged in shape. If `state.messages` is empty, skip the search (no query text) - `semantic_hits` defaults to `[]`.

- [ ] Step 1: Write the failing test - seed the backend with an entity observation via the write path for `compile_zip`, then send a `query_status` state with a matching prompt in `state.messages` -> assert `memory_context["semantic_hits"]` contains it; assert `memory_context["memory_bank"]` is unaffected in structure.
- [ ] Step 2: Run test to verify it fails.
- [ ] Step 3: Implement the read-path wiring.
- [ ] Step 4: Run test to verify it passes + full agent suite (all ~78 existing tests) stays green.
- [ ] Step 5: Commit - `git commit -m "feat(memory): semantic search on query_status read path (Phase 5a.6 Task 3)"`

---

### Task 4: mem0 Adapter (real backend, guarded, Ollama-only, opt-in)

**Files:**
- Create: `aiconnex_agent/memory/backends/mem0_adapter.py`
- Modify: `requirements.txt` or equivalent (add `mem0ai` as an OPTIONAL extra, not a hard pin in the base install - document the exact opt-in install command in a comment)
- Test: `tests/test_mem0_adapter.py` (uses `pytest.importorskip("mem0")` - skipped entirely unless `mem0ai` is actually installed AND Ollama is reachable; this test never runs in the default/CI-safe suite)

**Interfaces:**
- `Mem0Backend(SemanticMemoryBackend)`: constructs `mem0.Memory` via `Memory.from_config(...)` with:
  - `llm`: provider `ollama`, model from `OLLAMA_MODEL` env (reuse existing `aiconnex_agent/llm.py` env var, default consistent with that module).
  - `embedder`: provider `ollama`, model `nomic-embed-text` (default), `ollama_base_url` from `OLLAMA_BASE_URL`.
  - `vector_store`: provider `qdrant`, embedded on-disk `path` (e.g. `./.mem0_qdrant` inside the repo, gitignored), `embedding_model_dims: 768` (matches `nomic-embed-text`).
  - Sets `os.environ.setdefault("MEM0_TELEMETRY", "false")` before importing `mem0`.
  - `add(text, metadata)` -> `self._mem.add([{"role": "system", "content": text}], user_id=metadata.get("subject_id", "agent"), metadata=metadata)`.
  - `search(query, limit)` -> `self._mem.search(query, limit=limit)`, mapped into the common `{"text", "metadata", "score"}` result shape.
- Guarded top-level import: `try: from mem0 import Memory \n except ImportError: Memory = None`. `Mem0Backend.__init__` raises a clear `RuntimeError("mem0ai is not installed. Install with: pip install mem0ai")` if `Memory is None`, rather than an import-time crash for the whole `backends` package.

- [ ] Step 1: Write the failing/skippable test - `pytest.importorskip("mem0")`; if present, instantiate `Mem0Backend`, add one memory, search for it, assert a hit comes back. This test is expected to be SKIPPED in the default environment (mem0ai not installed here) - that is the correct, intended outcome, not a failure.
- [ ] Step 2: Run test to verify collection succeeds and it either skips (mem0ai absent) or fails meaningfully (mem0ai present but misconfigured).
- [ ] Step 3: Implement `Mem0Backend`.
- [ ] Step 4: Confirm: (a) full existing suite (~80+ tests) still passes with `mem0ai` NOT installed - `factory.py`/`local_fake.py` imports must not transitively require `mem0`; (b) if the developer chooses to `pip install mem0ai` locally and has Ollama running with `nomic-embed-text` pulled, the skipped test can be manually run and pass.
- [ ] Step 5: Commit - `git commit -m "feat(memory): mem0 adapter behind Ollama+Qdrant, guarded optional dependency (Phase 5a.6 Task 4)"`

---

## Plan Self-Review

1. **External prerequisite question answered directly:** No mem0 cloud account/API key needed. Two real new dependencies: the `mem0ai` package (pip, optional) and Qdrant (embedded on-disk mode needs no server setup). Both cited from official docs/source, not assumed.
2. **Guardrail preserved:** mem0 touches Entity memory only; Decision/Procedural routing code paths are explicitly untouched and covered by an isolation test (Task 2, Step 1).
3. **Zero-regression invariant:** every task's Step 4 re-runs the full existing suite; the mem0-adapter test is structured to SKIP (not fail, not run) when `mem0ai` is absent, which is the expected state of this repo today.
4. **Consistency with existing patterns:** `AICONNEX_MEMORY_BACKEND` env switch mirrors the already-planned `AICONNEX_LLM_BACKEND` switch; `get_semantic_backend()`/`reset_semantic_backend()` singleton mirrors `get_event_store()`/`reset_event_store()` from Phase 5a.1, including the same test-isolation concern (an autouse conftest reset should be added alongside if a real backend singleton is exercised across test files - flagged for Task 1 implementation).
5. **No placeholders:** every module has a concrete interface; the one deliberately-deferred piece (a live Qdrant Docker server for anything beyond local/embedded use) is explicitly named as out of scope for this task, not left ambiguous.

## Execution Choice

Plan saved to `docs/superpowers/plans/2026-07-29-phase5a6-mem0-sprint2.md`. Not started - awaiting go-ahead. Recommend Task 1-3 (interface + local fake + wiring) first since they need zero new installs, then decide separately whether to actually `pip install mem0ai` and pull an Ollama embedding model for Task 4.
