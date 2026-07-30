# AICONNEX Agentic Build: Phase 0 through Phase 5b — What We Did and How

**Branches:** `28_july_agentic` (Phase 0 - post-audit LLM fixes) → `mlflow-integration` (Phase 5b, branched off `28_july_agentic`)
**Status:** All committed and pushed. `mlflow-integration` pushed to `origin/mlflow-integration` as a new branch, to be merged back into `28_july_agentic` once 5b/5c are both done.
**Companion docs:** `docs/superpowers/plans/2026-07-29-agentic-branch-summary.md` (Phase 0-5a.6 detail), `docs/superpowers/plans/2026-07-29-phased-arch-audit.md` (real-vs-fake audit).

---

## The approach, in one paragraph

Every phase was built the same way: define the contract/interface first, wire it into the graph as a deterministic stub that just passes state through, verify the plumbing works, then replace the stub with real logic behind the exact same function signature. Nothing was built without a test proving it worked before moving to the next phase. This is why, when things went wrong mid-build (a branch switch silently reverting uncommitted work, a test hanging on a live network call, a hardcoded default silently overriding a real choice), the test suite caught it within the same session rather than surfacing as a mystery bug weeks later.

---

## Phase 0 — Pydantic Contracts

**What:** The 5-stage data contract pipeline, as pure Pydantic models with zero I/O and zero LLM calls:
- `ConversationUnderstandingContract` (CUC) — what the agent understands before any file is involved
- `ScoutEnrichedContract` — CUC plus upload/discovery/parser-selection info
- `PreCompilerContract` — the exact input handed to the compiler
- `DatasetIntelligenceContract` (DIC) — the compiler's structured output
- Later extended with `TaskStep`/`ExecutionPlan` (Phase 4) and `upload_path` (Phase 5b)

**How:** Wrote the schemas with every field carrying a `description=` so the contract is self-documenting. No behavior, just shape — this let every later phase be built and tested against a stable target.

**File:** `aiconnex_agent/schemas.py`

---

## Phase 1 — LangGraph Skeleton

**What:** The full graph topology — 7 nodes (`conversation_parser`, `clarification`, `planning_engine`, `scout_agent`, `platform_agent`, `memory_agent`, `plan_evaluator`), wired with conditional routing and a checkpointer, but every node was a deterministic stub that just logged and passed state through.

**How:** Built `MasterAgentState` (the single Pydantic model carrying all 5 contracts plus routing metadata) first, then `graph.py` wiring nodes with `add_conditional_edges`, then verified the full topology (`START → parser → route by confidence → clarification | planner → route by plan step → scout/platform/memory → evaluator → loop or END`) actually runs end-to-end with fake data before any real logic existed.

**Files:** `aiconnex_agent/state.py`, `aiconnex_agent/nodes/stub_nodes.py`, `aiconnex_agent/graph.py`, `aiconnex_agent/runner.py`

---

## Phase 2 — Terminal UI

**What:** A live Rich-based terminal dashboard (`agentic_terminla_UI/`) streaming graph execution in real time — a status/contract inspector panel and an agent telemetry stream panel.

**How:** Built against the already-proven stub graph from Phase 1 via `execute_and_stream()`, so any UI bug was isolated from graph logic by construction — the UI just renders whatever events the graph emits.

**Files:** `agentic_terminla_UI/components/status_inspector.py`, `dag_telemetry.py`, `tui_app.py`

---

## Phase 3 — Conversation Parser (first real logic)

**What:** Replaced the parser stub with 6 isolated sub-modules, each independently testable:
1. `PromptBuilder` — builds the system prompt sent to the LLM
2. `ContextManager` — tracks session/history across turns
3. `SemanticExtractor` — extracts intent/entities from the user's message
4. `StructuredOutputValidator` — validates extracted data against the CUC schema
5. `ConfidenceScorer` — scores how confident the extraction is
6. `ClarificationGenerator` — writes a follow-up question when confidence is low

**How (first pass):** All 6 were built heuristic-first — regex/keyword matching, fixed if/elif ladders, template sentences — to prove the pipeline shape worked before adding any LLM dependency.

**How (later, post-audit real-LLM upgrade):** `SemanticExtractor`, `ConfidenceScorer`, and `ClarificationGenerator` were each converted to make a real call to `get_llm()` (Ollama Cloud, `gpt-oss:120b-cloud`) as the primary path, with their original heuristic logic kept ONLY as a fallback triggered by a genuine failure (network error, or the LLM returning something invalid/out-of-range/hallucinated). The clarification node itself was also rewired — it used to hardcode "Which processing mode would you like?" regardless of context; now it calls the real `ClarificationGenerator` and asks about whatever is actually missing.

**Files:** `aiconnex_agent/parser/` (6 modules + `conversation_parser.py` orchestrator + `clarification_node.py`)

---

## Phase 4 — Planning Engine

**What:** Replaced the planning stub with real intent → execution-plan routing, via 2 sub-modules:
- `IntentPlanMapper` — a fixed lookup table (`compile_zip` → scout+memory; `train_rul`/`detect_anomalies` → scout+platform+memory; `query_status` → memory only; unknown → scout fallback)
- `PlanValidator` — turns raw steps into a validated `ExecutionPlan`, guaranteeing a non-empty, routable plan

**How:** Built as a deterministic lookup table by deliberate choice, not an LLM call — routing "which agent handles this" is a fixed business rule, not a judgment call, so it needed to be 100%-reliable and instantly unit-testable.

**Files:** `aiconnex_agent/planning/` (`intent_plan_mapper.py`, `plan_validator.py`, `planning_engine.py`)

---

## Phase 5a — Memory Agent (event-sourced)

**What:** Replaced the memory stub with a full event-sourcing subsystem, built in 6 stages:
- **5a.1** — Event taxonomy (`BaseEvent`) + append-only `EventStore`
- **5a.2** — 4 separate memory products (Session/Entity/Procedural/Decision) + a deterministic `MemoryPolicyEngine` deciding what gets kept, summarized, or discarded per event type
- **5a.3** — `MemoryBuilder`: a pure function projecting the full event log into the 4 memory layers (never a direct write)
- **5a.4** — `real_memory_agent_node`: writes events implied by what upstream nodes produced, reads back a rebuilt memory bank
- **5a.5** — Replay/rebuild (`rebuild_memory_from_events`, `replay_workflow`, `explain_fact`) — proves any memory fact can be traced back to the exact event that produced it
- **5a.6** — mem0 semantic search layered behind Entity memory ONLY (`LocalFakeBackend` as the default test double, `Mem0Backend` as the real production adapter using Ollama for extraction and embeddings, embedded on-disk Qdrant for storage)

**How:** Built memory as a derived product of an auditable log, not a side effect buried in agent code — the same principle applied consistently: an audit trail must never fail non-deterministically, so LLM judgment (mem0's fuzzy search) sits strictly on top of this substrate, never inside the write path.

**Files:** `aiconnex_agent/memory/` (`events.py`, `event_store.py`, `memory_layers.py`, `policy_engine.py`, `memory_builder.py`, `memory_agent.py`, `replay.py`, `backends/`)

---

## Cross-cutting: LLM Backend Switch

**What:** `get_llm()` in `aiconnex_agent/llm.py` — one entry point every real-LLM module calls through, switching between Ollama (default) and OpenAI (opt-in) via `AICONNEX_LLM_BACKEND`.

**How:** Kept on Ollama Cloud (`gpt-oss:120b-cloud`) by explicit decision — model quality prioritized over local latency, even though it requires an active `ollama.com` sign-in and network access for every call.

---

## Phase 5b — Scout Agent (real UnifiedCompiler integration)

**Starting point:** A full audit (`2026-07-29-phased-arch-audit.md`) found `stub_scout_agent_node` was still hardcoding `"suyash2.zip"` and a fixed file inventory regardless of what was actually uploaded — the single biggest gap in the whole system, since it meant the agent could confidently report fake results.

**Investigation before building anything:** Rather than assume what existed, a context-gathering pass across the actual code on this branch found:
- The old `ScoutAgent` 3-method assistive class (`inspect`/`advise_strategy`/`self_heal`) had been deleted on a prior branch before that branch was merged in — its 2 test files were broken (`ImportError` on collection), referencing a class that no longer existed anywhere in the tree.
- `UnifiedCompiler` (the real 5-stage plugin pipeline compiler in `aiconnex_zip_compiler/`) never actually depended on `ScoutAgent` — `scout=None` was already a fully supported, tested path.
- No adapter existed translating the compiler's plain dataclass output (`CompileResult`) into the agent's Pydantic contracts.
- The compiler's internal "HITL Intent Layer" (`IntentClassifier`/`IntentResolver`) was actually a deterministic heuristic engine with no LLM call at all, despite its name — and despite claiming to be "human in the loop," it always silently auto-picked the first option without ever truly pausing.

**Gaps identified and resolved, before writing the Scout node itself:**

1. **No real file path reached the agent.** Added `upload_path: Optional[str]` to `MasterAgentState`. Wired through `run_tui_session()` too, so the TUI entry point can pass a real file, not just a prompt string.
2. **No adapter between compiler output and agent contracts.** Built `aiconnex_agent/scout/compiler_adapter.py` — translates `CompileResult`/`dataset_card.json` into `ScoutEnrichedContract`/`DatasetIntelligenceContract` fields: real row/column counts (read directly from the compiled CSV), real dataset name/domain (read from the compiler's own dataset card), real quality warnings (from the compiler's join audits).
3. **Compile failures had no defined handling.** Scout now retries the compile once (covers transient failures), and if it still fails, raises a real LangGraph clarification interrupt asking the user to check the file and re-upload — instead of silently proceeding with an empty/fake DIC.
4. **`CompilerRequest` fields were decorative.** `infer_targets`/`infer_problem_candidates` now actually control the real `enable_intelligence` parameter passed into `UnifiedCompiler`.
5. **The compiler's own LLM intelligence layer was dead** (deleted in a prior merge, silently swallowed as a warning). Deliberately left unfixed for 5b — `problem_candidates`/`target_candidates`/`feature_catalog` stay empty rather than faked, deferred to whenever Platform (5c) has real modeling context to justify rebuilding it.
6. **No decision on where compiled output lives.** Resolved pragmatically: one session-scoped folder per workflow under `scratch/scout_output/<workflow_id>/` — the exact location doesn't matter since the DIC's `output_path`/`combined_csv_path` fields are the retrieval pointer, not the folder convention.
7. **The compiler silently auto-picked the first strategy whenever 2+ genuinely different options existed** (e.g. "one unified model across all conditions" vs "one model per condition") — a real decision being made for the user without asking. Built `aiconnex_agent/scout/strategy_peek.py`: runs the SAME `CardGenerator`+`IntentClassifier` steps the compiler runs internally, standalone, before committing to a full compile. If only 1 option exists, nothing to ask — proceed silently. If 2+ exist, Scout raises a real LangGraph clarification with the actual option labels, then passes the user's answer back into `UnifiedCompiler(strategy_override=...)`.

**The Scout node itself** (`aiconnex_agent/scout/scout_node.py`): reads `state.upload_path`, peeks at real strategy options (gap 7), retries+flags on failure (gap 3), calls `UnifiedCompiler` with real `CompilerRequest` flags (gap 4), and adapts the real result into contracts (gap 2). Wired into the graph via the same delegation pattern as every other real node: `stub_scout_agent_node` now just calls `real_scout_agent_node`.

**Verification — proven against real datasets, not just synthetic test fixtures:**
- 7 dedicated tests covering each gap individually (missing file, real compile success, retry-then-flag on failure, `CompilerRequest` flags reaching the compiler, multi-strategy interrupt firing, single-strategy interrupt NOT firing)
- 4 existing tests updated to provide real synthetic zips instead of relying on the old stub's fake data (`test_stub_nodes.py`, `test_langgraph_topology.py`, `test_graph_runner.py`, `test_tui_app.py`)
- Manually run against `data/raw/suyash2.zip` (real 7.4MB file): correctly detected 2 real strategies and asked, then compiled **7684 rows, 262 columns** — nothing close to the old hardcoded fake `26898`/`253`
- Manually run against the real NASA C-MAPSS zip: correctly detected the unified-vs-per-condition fork, compiled **265,963 rows, 28 columns**
- Full regression suite: only 2 pre-existing failures remain, both confirmed via `git stash` to predate this work entirely (same root cause: the dead intelligence-layer module from an old merge)

**Files:** `aiconnex_agent/scout/` (`scout_node.py`, `compiler_adapter.py`, `strategy_peek.py`)

---

## Incidents encountered and resolved across the whole build

1. **`SemanticExtractor`'s `"zip"` substring bug** — checking `compile_zip` keywords first meant any `.zip` filename mention hijacked prompts actually about training/anomaly-detection into the wrong intent. Fixed by reordering checks most-specific-first.
2. **Singleton test pollution** — `EventStore` and `SemanticMemoryBackend` are process-wide singletons; running the full graph in one test leaked state into the next test in the same pytest session. Fixed with autouse `reset_*()` fixtures.
3. **Uncommitted work lost to a branch switch** — Phase 4's schema additions and an 8-file legacy-node cleanup were sitting uncommitted when a branch switch silently reverted them. Rebuilt and re-committed; this is the direct reason every phase since has been committed immediately rather than batched.
4. **mem0 live-network test started hanging** once `mem0ai` was actually installed mid-session, since `pytest.importorskip` alone isn't a safe enough gate for a real network call. Fixed with an explicit `AICONNEX_RUN_LIVE_MEM0_TESTS=1` opt-in flag.
5. **mem0 was forcing an unnecessary separate local model** (`llama3.1`), contradicting the decision to keep the main agent on the cloud model for quality. Fixed to reuse `OLLAMA_MODEL`.
6. **The old `ScoutAgent`/`patch_proposer`/`sandbox_runner` modules were already deleted on this branch, but their tests weren't.** 6 tests across 2 files broke test collection. Deleted the broken tests rather than reviving a self-patching-code subsystem that was never in scope for 5b.
7. **The compiler's dead intelligence layer surfaces as a recurring, pre-existing landmine** — `test_intelligence_layer.py`, `test_orchestrator_two_pass.py`, and `test_prompter_tui.py` all break collection on `from aiconnex_zip_compiler.intelligence...` imports that no longer resolve. Confirmed via `git stash` this predates all of this session's work. Flagged, not yet fixed — out of scope for 5b, candidate for a dedicated gap-5 cleanup pass.

---

## Test coverage at end of Phase 5b

`tests/` (excluding the pre-broken `test_intelligence_layer.py` collection error): all real Scout/parser/planning/memory tests passing. Only 2 failures remain, both pre-existing and unrelated (`test_cli.py::test_invalid_strategy_warns_and_falls_back`, `test_multi_format.py::test_excel_and_json_compilation`), confirmed via `git stash` comparison to exist before any of this session's changes.

`aiconnex_zip_compiler/tests/`: passing except 2 pre-existing `PluginRegistry.unfreeze()`/`reload_and_unfreeze()` AttributeErrors (methods that don't exist on the current class) and the same dead-intelligence-module collection breaks in `test_orchestrator_two_pass.py`/`test_prompter_tui.py`.

---

## Commit reference

`28_july_agentic` (Phase 0 through post-audit fixes) commits are listed in `2026-07-29-agentic-branch-summary.md`. `mlflow-integration` (branched from `28_july_agentic` at `4c0b146`) Phase 5b commits, in order:

- `a281e29` — remove 4 broken tests referencing deleted ScoutAgent/patch_proposer/sandbox_runner
- `edac1f6` — delete test_scout_integration.py (fully dependent on deleted ScoutAgent)
- `164bb43` — Phase 5b: real UnifiedCompiler-backed Scout node (gaps 1, 2, 3, 4, 7)
- `a8df59f` — docs: sync context_log.md

Pushed to `origin/mlflow-integration` (new branch, no prior remote history to reconcile). Not yet merged back into `28_july_agentic` - planned once Phase 5c (Platform Agent) is also complete.
