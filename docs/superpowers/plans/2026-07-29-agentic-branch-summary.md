# AICONNEX Agentic LangGraph Build — Branch Summary

**Branch:** `28_july_agentic`
**Scope:** The full phased build of the LangGraph agentic layer, from Phase 0 (Pydantic contracts) through the post-audit real-LLM conversion fixes.
**Status at time of writing:** All work committed and pushed to `origin/28_july_agentic` (HEAD `530ad61`).
**Companion doc:** `docs/superpowers/plans/2026-07-29-phased-arch-audit.md` — the real-vs-fake audit that drove the final round of fixes described here.

---

## The core principle behind the whole build

Never build a component you can't immediately test in isolation. Each phase produced a runnable, testable artifact before the next phase started — Pydantic contracts before the graph, stub nodes before real logic, deterministic fallbacks before LLM calls. This discipline is why, when a branch-switch incident later reverted some uncommitted work, the damage was caught in seconds by the test suite rather than discovered days later.

---

## Phase 0 — Pydantic Contracts

**What:** The 5-stage canonical contract pipeline as pure data models, zero I/O, zero LLM calls.
- `ConversationUnderstandingContract` (CUC — pre-upload)
- `ScoutEnrichedContract` (during upload)
- `PreCompilerContract` (input to the compiler)
- `DatasetIntelligenceContract` (DIC — post-compiler output)
- Later extended with `TaskStep` / `ExecutionPlan` (Phase 4)

**File:** `aiconnex_agent/schemas.py`

---

## Phase 1 — LangGraph Skeleton

**What:** The full StateGraph topology wired with deterministic stub nodes that log and pass state through — no LLM calls, no real logic. This validated the plumbing (state flow, conditional routing, `interrupt()`, checkpointing) before anything real was built on top.

**Files:** `aiconnex_agent/state.py` (`MasterAgentState`), `aiconnex_agent/nodes/stub_nodes.py` (7 stub nodes), `aiconnex_agent/graph.py`, `aiconnex_agent/runner.py`

**Flow:** `START → conversation_parser_node → (confidence-based route) → clarification_node | planning_engine_node → route_agent → scout/platform/memory_agent_node → plan_evaluator_node → (loop or END)`

---

## Phase 2 — Terminal UI

**What:** A live Rich-based terminal dashboard streaming `astream_events()` from the graph — a status/contract inspector panel and an agent telemetry stream panel, built against the already-proven stub graph so any UI bug was isolated from graph logic.

**Files:** `agentic_terminla_UI/components/status_inspector.py`, `dag_telemetry.py`, `tui_app.py`

---

## Phase 3 — Conversation Parser (first real node)

**What:** The first user-facing real logic, built as 6 isolated sub-modules:
1. `PromptBuilder` — system prompt construction
2. `ContextManager` — session/history tracking
3. `SemanticExtractor` — intent/entity extraction (originally heuristic-only; **upgraded later in this session to a real LLM call**, see "Post-audit fixes" below)
4. `StructuredOutputValidator` — Pydantic validation of extracted data
5. `ConfidenceScorer` — confidence scoring (originally a rule-based ladder; **later upgraded**)
6. `ClarificationGenerator` — clarifying-question generation (originally template strings; **later upgraded**)

**Files:** `aiconnex_agent/parser/` (6 modules) + `conversation_parser.py` orchestrator

---

## Phase 4 — Planning Engine

**What:** Real intent → routed execution plan logic, replacing the planning stub. Built as 2 isolated sub-modules:
- `IntentPlanMapper` — deterministic lookup table (`compile_zip` → scout+memory; `train_rul`/`detect_anomalies` → scout+platform+memory; `query_status` → memory only; unknown → scout fallback)
- `PlanValidator` — validates raw plan steps into a typed `ExecutionPlan`, guarantees a non-empty routable plan

**Design decision:** Kept deliberately deterministic, not LLM-based — routing "which agent handles what" is a fixed business rule, not a judgment call, so it needed to be 100% unit-testable with zero LLM dependency.

**Files:** `aiconnex_agent/planning/` (`intent_plan_mapper.py`, `plan_validator.py`, `planning_engine.py`)

**Note:** This phase's work was initially lost to an uncommitted-changes/branch-switch incident (see "Incidents" below) and had to be rebuilt from memory and re-committed.

---

## Phase 5a — Memory Agent (event-sourced)

**What:** Replaced the memory stub with a full event-sourcing subsystem — memory as a *derived product of an auditable event log*, not a side effect buried in agent code. Built in 5 isolated stages (Sprint 1, all deterministic):

- **5a.1** — Event taxonomy (`BaseEvent`) + append-only `EventStore`
- **5a.2** — 4 separate memory products (`SessionMemory`, `EntityMemory`, `ProceduralMemory`, `DecisionMemory`) + `MemoryPolicyEngine` (deterministic retention rules per event type)
- **5a.3** — `MemoryBuilder`: pure, idempotent projection of the event log into the 4 memory layers
- **5a.4** — `real_memory_agent_node`: write path (records events from what upstream nodes produced) + read path (`query_status`, never duplicates events)
- **5a.5** — Replay/rebuild (`rebuild_memory_from_events`, `replay_workflow`, `explain_fact`) — proves memory is always re-derivable from the log + policy, never independently mutated state

**Design decision:** Same rationale as Planning Engine — an audit trail must never fail non-deterministically, so LLM judgment sits on top of this substrate, never inside the write path.

**Files:** `aiconnex_agent/memory/` (`events.py`, `event_store.py`, `memory_layers.py`, `policy_engine.py`, `memory_builder.py`, `memory_agent.py`, `replay.py`)

---

## Phase 5a.6 — mem0 Semantic Memory (Sprint 2)

**What:** A fuzzy, natural-language recall layer sitting BEHIND the Entity memory layer only — Decision and Procedural memory stay fully deterministic on principle (a decision's provenance must never depend on non-deterministic LLM extraction). Built in 4 tasks:

- **Task 1** — `SemanticMemoryBackend` interface + `LocalFakeBackend` (zero-LLM keyword-overlap test double, the default backend) + `Mem0Backend` (real production adapter)
- **Task 2** — Wired into `MemoryBuilder`'s Entity-layer routing only, with an isolation test proving Decision/Procedural paths never call it
- **Task 3** — Wired into the `query_status` read path, output kept in a separate `memory_context["semantic_hits"]` key, never blended with the deterministic memory bank
- **Task 4** — The real `Mem0Backend`: Ollama (embedder: `nomic-embed-text`, extraction LLM: reuses the same `OLLAMA_MODEL` as the rest of the agent) + embedded on-disk Qdrant. No cloud account, no API key required.

**External configuration completed:** `pip install mem0ai`, `ollama pull nomic-embed-text` — both done. **Not yet activated** — `AICONNEX_MEMORY_BACKEND` is still unset, so `LocalFakeBackend` remains the live default.

**Files:** `aiconnex_agent/memory/backends/` (`base.py`, `local_fake.py`, `factory.py`, `mem0_adapter.py`)

---

## Cross-cutting: LLM Backend Switch

**What:** `get_llm()` in `aiconnex_agent/llm.py` — a single entry point switching between Ollama (default) and OpenAI (opt-in) via `AICONNEX_LLM_BACKEND`. Kept on Ollama Cloud (`gpt-oss:120b-cloud`) by explicit decision — model quality prioritized over local latency, even though it requires an active `ollama.com` sign-in.

---

## Post-audit fixes: closing the "still heuristic" gaps

A full audit (`docs/superpowers/plans/2026-07-29-phased-arch-audit.md`) was performed by reading every module fresh rather than trusting memory. It found that 3 sub-modules built in Phase 3 were still running on placeholder logic despite the parser's "first LLM call" module (`SemanticExtractor`) already having been upgraded:

1. **`stub_clarification_node`** — was hardcoded to always ask "Which processing mode would you like?" regardless of what was actually ambiguous, completely bypassing the real `ClarificationGenerator`. Fixed by building `real_clarification_node`, wired via the same delegation pattern used elsewhere.
2. **`ConfidenceScorer`** — was a fixed if/elif ladder (0.95/0.88/0.86/0.50). Converted to a real LLM self-assessment call, with the ladder kept only as a fallback for network failure or an out-of-range/hallucinated score.
3. **`ClarificationGenerator`** — was 3 fixed sentence templates. Converted to a real LLM call composing questions targeted at the actual gaps in the CUC, with the templates kept only as a fallback.

All three follow the same pattern as `SemanticExtractor`: real LLM call first, strict validation of the response (reject hallucinations/out-of-range values), deterministic fallback only on genuine failure — never as the default path.

---

## What is genuinely real vs. deliberately deterministic vs. still fake (as of this doc)

**Real (LLM-backed):** `SemanticExtractor`, `ConfidenceScorer`, `ClarificationGenerator`, the real clarification node.

**Deterministic by explicit design (not gaps):** Planning Engine routing, Memory Policy Engine retention rules, structured output/schema validation.

**Still stub/fake — the two largest remaining gaps:**
- **Phase 5b (not started):** Scout Agent — still returns hardcoded fake dataset info (`suyash2.zip`, fixed file inventory) regardless of what's actually uploaded. Needs a real `UnifiedCompiler` integration.
- **Phase 5c (not started):** Platform Agent — still returns hardcoded fake training results (`26898 rows`, fixed dataset identity) regardless of the actual plan. Needs a real `aiconnex_ml` training integration.

---

## Incidents encountered and resolved during the build

1. **`SemanticExtractor`'s `"zip"` keyword bug** — the original heuristic checked `compile_zip` keywords first, and the bare substring `"zip"` matched inside any `.zip` filename mention, hijacking prompts that were actually about training or anomaly detection into the wrong intent. Fixed by reordering the check to most-specific-first.
2. **`EventStore` / `SemanticMemoryBackend` singleton test pollution** — both are process-wide singletons; running the full graph in one test file leaked state into whatever test ran next in the same pytest session. Fixed with autouse `reset_*()` fixtures in `tests/conftest.py`.
3. **Uncommitted work lost to a branch switch** — Phase 4's `TaskStep`/`ExecutionPlan` schema additions and the 8-file legacy-node cleanup were sitting uncommitted when a branch switch (to `bug-fix-for-satish_data` and back) silently reverted them. Both were rebuilt and re-committed. This is the direct motivation for committing every phase immediately rather than batching commits.
4. **mem0 live-network test hang** — a test gated only by `pytest.importorskip("mem0")` started hanging once `mem0ai` was actually installed mid-session, since the package's mere presence isn't a safe enough gate for a real network/model call. Fixed with an explicit `AICONNEX_RUN_LIVE_MEM0_TESTS=1` opt-in flag, independent of package installation state.
5. **mem0 forcing an unnecessary local model** — `Mem0Backend` originally forced a separate `llama3.1` pull for its extraction LLM, contradicting the explicit decision to keep the main agent on the cloud model for quality. Fixed to reuse `OLLAMA_MODEL` (the same cloud model) — only the embedder genuinely needs a local pull, since Ollama Cloud doesn't serve embeddings.

---

## Test coverage

Final state: **117 tests passing, 1 intentionally skipped** (the live mem0+Ollama+Qdrant roundtrip, gated behind an explicit opt-in flag). Every phase was built test-first — write the failing test, verify it fails for the right reason, implement, verify it passes, run the full regression suite, commit.

---

## Commit reference

All of the above is committed on `28_july_agentic` and pushed to `origin/28_july_agentic` (HEAD `530ad61` at time of writing). Key milestone commits, in order:

- `a278285` → `7646594` — Phases 1-2 (state, stub nodes, graph, runner, TUI)
- `2989322` → `c0d9d39` — Phase 3 (Conversation Parser, 6 sub-modules)
- `92e7322` — Phase 4 (Planning Engine)
- `388ce88` → `aaf8cac` — Phase 5a Sprint 1 (Memory Agent, deterministic core)
- `85df7e9` → `46be37a` — Phase 5a.6 Sprint 2 (mem0 semantic backend)
- `5707de5` — LLM backend switch
- `7ee8bab` — `SemanticExtractor` real LLM call
- `9036948` — Architecture audit (reference commit)
- `215f355` — `ConfidenceScorer` + `ClarificationGenerator` + real clarification node (audit fixes)
