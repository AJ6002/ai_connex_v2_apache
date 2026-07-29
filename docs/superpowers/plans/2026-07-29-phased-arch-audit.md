# AICONNEX Agentic Architecture — Phased Build Audit

**Branch:** `28_july_agentic`
**Audit performed:** by reading every module fresh (not from memory), verified via full test run (107 passed, 1 intentionally skipped) and `git log`.
**Reference commit for this audit:** see bottom of file.

---

## Phase-by-phase status

| Phase | Component | Status | Real or Fake/Stub | Notes |
|---|---|---|---|---|
| 0 | Pydantic contracts (`schemas.py`) | ✅ Done | Real | CUC, ScoutEnriched, PreCompiler, DIC + Phase 4's `TaskStep`/`ExecutionPlan` |
| 1 | LangGraph skeleton (`state.py`, `graph.py`, `stub_nodes.py`) | ✅ Done | Real (topology) | Graph wiring, checkpointer, conditional routing all real and unchanged since Phase 1 |
| 1 | `stub_conversation_parser_node` | ✅ Done | **Real** | Delegates to `real_conversation_parser_node` |
| 1 | `stub_clarification_node` | ⚠️ **Still fake** | **Fake** | Hardcodes `"Which processing mode would you like?"` — ignores the real `ClarificationGenerator` built in Phase 3. Flagged, not yet fixed. |
| 1 | `stub_planning_engine_node` | ✅ Done | **Real** | Delegates to `real_planning_engine_node` (Phase 4) |
| 1 | `stub_scout_agent_node` | ❌ Not started | **Fake** | Hardcoded `"suyash2.zip"` / `"suyash2.csv"` regardless of input. No real `UnifiedCompiler` call. This is Phase 5b. |
| 1 | `stub_platform_agent_node` | ❌ Not started | **Fake** | Hardcoded `"Suyash2 Telemetry"`, `26898 rows`. No real ML training call. This is Phase 5c. |
| 1 | `stub_memory_agent_node` | ✅ Done | **Real** | Delegates to `real_memory_agent_node` (Phase 5a) |
| 1 | `stub_plan_evaluator_node` | ✅ Done | Real | Genuine step-index bookkeeping, not actually a stub despite the name |
| 2 | Terminal UI (`agentic_terminla_UI/`) | ✅ Done | Real | Status inspector + DAG telemetry, wired to `execute_and_stream()` |
| 3 | Conversation Parser — `PromptBuilder` | ✅ Done | Real | Pure string formatting |
| 3 | Conversation Parser — `ContextManager` | ✅ Done | Real | In-memory session/history tracking |
| 3 | Conversation Parser — `SemanticExtractor` | ✅ **Fixed this session** | **Real LLM call** | Now calls `get_llm()` by default (`use_llm=True`); validates response, rejects hallucinated intents; heuristic is fallback-only on network/parse failure |
| 3 | Conversation Parser — `StructuredOutputValidator` | ✅ Done | Real | Pydantic schema validation, deterministic by design (validation is not a judgment call) |
| 3 | Conversation Parser — `ConfidenceScorer` | ⚠️ **Not yet converted** | **Rule-based, not LLM** | Fixed if/elif ladder returning static scores (0.95/0.88/0.86/0.50). User has asked for "no heuristics, still" — flagged for conversion to a real LLM self-assessment call with fallback. |
| 3 | Conversation Parser — `ClarificationGenerator` | ⚠️ **Not yet converted, and not even wired in** | **Template-based, not LLM** | Picks from 3 fixed sentence templates. Also disconnected from the graph (see `stub_clarification_node` above). |
| 4 | Planning Engine (`IntentPlanMapper`, `PlanValidator`, `real_planning_engine_node`) | ✅ Done | **Deterministic by design** | Explicit decision: routing "which agent handles what" is a fixed business rule, not a judgment call — kept LLM-free on purpose, same rationale as the Memory Policy Engine |
| 5a | Memory Agent — `EventStore`, `MemoryPolicyEngine`, `MemoryBuilder` | ✅ Done | **Deterministic by design** | Explicit decision: an audit trail must never fail non-deterministically; LLM judgment sits on top, never inside the write path |
| 5a | Memory Agent — `real_memory_agent_node` | ✅ Done | Real | Write path (events) + read path (`query_status`), wired into the graph |
| 5a | Memory Agent — Replay (`replay.py`) | ✅ Done | Real | `rebuild_memory_from_events`, `replay_workflow`, `explain_fact` |
| 5a.6 | Semantic memory backend — `LocalFakeBackend` | ✅ Done (intentional test double) | **Fake, by design, default** | Keyword-overlap match. Default backend (`AICONNEX_MEMORY_BACKEND` unset) — this is what actually runs today. |
| 5a.6 | Semantic memory backend — `Mem0Backend` | ✅ Built, **not yet activated** | **Real, dormant** | Fully coded: reuses `OLLAMA_MODEL` (gpt-oss:120b-cloud) for extraction, `nomic-embed-text` for embeddings (pulled locally, confirmed today), embedded on-disk Qdrant. Requires `AICONNEX_MEMORY_BACKEND=mem0` to activate — currently unset, so `LocalFakeBackend` is what's live. |
| 5b | Scout Agent (real `UnifiedCompiler` calls) | ❌ **Not started** | Fake (stub) | Next planned phase |
| 5c | Platform Agent (real `aiconnex_ml` training) | ❌ **Not started** | Fake (stub) | Planned after 5b |
| — | LLM backend switch (`aiconnex_agent/llm.py`) | ✅ Done | Real | `get_llm()` switches Ollama/OpenAI via `AICONNEX_LLM_BACKEND` (default `ollama`, kept as `gpt-oss:120b-cloud` per explicit decision — quality over local latency) |

---

## What is genuinely real right now (if you ran a live conversation through this agent)

1. Your prompt would be parsed by a **real LLM call** (Ollama Cloud, `gpt-oss:120b-cloud`) to extract intent/entities, with hallucination rejection and heuristic fallback on failure.
2. The extracted intent would be routed by the **real, deterministic Planning Engine** into a correct multi-step plan (`compile_zip` → scout+memory; `train_rul`/`detect_anomalies` → scout+platform+memory; `query_status` → memory only).
3. Memory writes/reads are **real and event-sourced** — every step gets recorded as an auditable event, replayable, provenance-traceable.
4. Semantic memory search runs on a **fake keyword-matcher** today (`LocalFakeBackend`) — the real `Mem0Backend` exists but is dormant.
5. **Whatever Scout/Platform were supposed to actually do — compile a real ZIP, train a real model — never happens.** The agent would confidently report back fake, hardcoded results (`suyash2.zip`, `26898 rows`) regardless of what was actually asked or uploaded.
6. If the parser's confidence drops below 0.85, the clarification step fires — but asks a **hardcoded, generic question**, not one derived from what's actually ambiguous in the request.

## Deliberately deterministic (not gaps — explicit design decisions, discussed and agreed)

- Planning Engine routing table
- Memory Policy Engine retention rules
- Structured output validation (Pydantic schema checks)

## Genuine gaps still open (heuristic/fake where a real LLM call or real agent action was intended)

1. `stub_clarification_node` → wire to real `ClarificationGenerator` (small fix, no external deps)
2. `ConfidenceScorer` → convert to real LLM self-assessment call (no external deps)
3. `ClarificationGenerator` → convert to real LLM-generated questions (no external deps)
4. Phase 5b Scout Agent → real `UnifiedCompiler` integration (largest remaining phase)
5. Phase 5c Platform Agent → real `aiconnex_ml` training integration (largest remaining phase)
6. mem0 activation → flip `AICONNEX_MEMORY_BACKEND=mem0` once ready (embedder already pulled; extraction LLM already reuses cloud model — no further external config needed beyond that one env var + confirming `mem0ai` stays installed)

## External configuration already done

- `pip install mem0ai` — confirmed installed
- `ollama pull nomic-embed-text` — confirmed pulled (274MB, verified via `ollama list`)
- `ollama signin` — presumed active (existing cloud models already in use)

## External configuration still pending, if/when needed

- None required to proceed with gaps 1-3 or 5b/5c planning.
- Gap 6 (mem0 activation) needs no new installs — just setting `AICONNEX_MEMORY_BACKEND=mem0`, at your discretion.

## Verification performed for this audit

- Full test suite run: `107 passed, 1 skipped` (skip is intentional — live mem0 network test, gated behind `AICONNEX_RUN_LIVE_MEM0_TESTS=1`)
- Confirmed via `git log` that all listed "Done" items have corresponding commits on `28_july_agentic`
- Caught and fixed a real regression during this audit cycle: a branch switch (`bug-fix-for-satish_data` → `28_july_agentic`) had silently reverted uncommitted Phase 4 schema additions and the 8-file legacy-node cleanup, both now re-applied and committed
