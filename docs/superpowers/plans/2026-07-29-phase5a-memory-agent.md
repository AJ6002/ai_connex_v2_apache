# Phase 5a: Event-Sourced Memory Agent (Sprints 1 & 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `stub_memory_agent_node` with a real, event-sourced memory subsystem. Memory becomes a *derived product of an auditable append-only event log*, not a side-effect buried inside agents. Sprint 1 (5a.1-5a.5) is fully deterministic and zero-LLM/zero-network. Sprint 2 (5a.6) adds mem0 as a semantic search index behind the Entity memory layer only.

**Core principle (unchanged from Phases 0-4):** never build a component you can't immediately test in isolation. The Event Store is the reliable substrate that can never fail non-deterministically; LLM judgment (mem0) sits on top of it as a consumer, never inside the write path.

**Architecture:** New package `aiconnex_agent/memory/`, mirroring the isolated-sub-module convention of `aiconnex_agent/parser/` (6 modules) and `aiconnex_agent/planning/` (2 modules):

| Module | Responsibility | LLM/IO |
|---|---|---|
| `events.py` | Event taxonomy - `BaseEvent` + typed event families | none |
| `event_store.py` | `EventStore`: append-only log, pluggable backend (in-memory default, JSONL file optional) | file IO only (optional) |
| `memory_layers.py` | Pydantic models for the 4 memory products + `MemoryBank` aggregate | none |
| `policy_engine.py` | `MemoryPolicyEngine`: deterministic `event -> RetentionDecision` | none |
| `memory_builder.py` | `MemoryBuilder`: projects an event log into the 4 memory layers | none |
| `replay.py` | `rebuild_memory_from_events`: pure re-projection for auditability | none |
| `memory_agent.py` | `real_memory_agent_node`: orchestrates store + policy + builder; write path & read path | none (Sprint 1) |
| `backends/mem0_adapter.py` + `backends/local_fake.py` | Sprint 2: semantic index behind Entity memory layer, with deterministic fake for tests | LLM+network (real) / none (fake) |

**Integration:** `stub_memory_agent_node` delegates to `real_memory_agent_node`, identical to how `stub_planning_engine_node` delegates to `real_planning_engine_node`. `graph.py` topology, `route_agent`, and `route_after_evaluator` require ZERO changes - the node keeps returning `{"memory_context": {...}, "active_agent": "evaluator"}`.

## Global Constraints
- Sprint 1 is 100% deterministic: zero LLM calls, zero network. Optional file IO for JSONL persistence only, disabled in tests (in-memory backend).
- Event Store is append-only and immutable: no update/delete of recorded events. Memory is rebuilt by re-projection, never by mutating events.
- The 4 memory layers stay separate products (Session / Entity / Procedural / Decision). No single "vague vector blob."
- `MasterAgentState.memory_context` stays typed `Dict[str, Any]` - no state schema migration. The `MemoryBank` is serialized into `memory_context` as plain dicts on the way out.
- Test isolation: `real_memory_agent_node` uses a module-level default `EventStore` accessed via `get_event_store()` / `reset_event_store()`, so each test starts from a clean store (same singleton-with-reset pattern used elsewhere).
- 100% test coverage per module + a node-level integration test covering both the write path (compile/train plans) and read path (`query_status`).
- Sprint 2 (mem0) never becomes a hard dependency of Sprint 1 tests: it sits behind an adapter interface with a deterministic local fake, mirroring the `AICONNEX_DISABLE_LLM=1` fallback pattern already used in the parser.

---

### Task 5a.1: Event Taxonomy + Event Store

**Files:**
- Create: `aiconnex_agent/memory/__init__.py`
- Create: `aiconnex_agent/memory/events.py`
- Create: `aiconnex_agent/memory/event_store.py`
- Test: `tests/test_memory_event_store.py`

**Event shape (`BaseEvent`):** `event_id: str`, `event_type: str`, `timestamp: str` (ISO 8601), `workflow_id: str`, `agent: str`, `subject_type: str`, `subject_id: str`, `payload: Dict[str, Any]`, `outcome: str` (`success | failure | pending`).

**Event families & concrete types (mapped to the graph nodes that emit them):**

| Family | event_type | Emitting node |
|---|---|---|
| Conversation | `ConversationParsed` | conversation_parser_node |
| HITL Decision | `ClarificationRequested`, `ClarificationAnswered` | clarification_node |
| Planning | `PlanCreated` | planning_engine_node |
| Upload | `ArchiveUploaded` | scout_agent_node |
| Parsing | `ArchiveDiscovered`, `ParserSelected` | scout_agent_node |
| Compilation | `DatasetCompiled` | scout/platform_agent_node |
| Training | `ModelTrained` | platform_agent_node |
| Evaluation | `ModelEvaluated` | platform_agent_node |
| Deployment | `ModelDeployed` | (future) |

**Interfaces:**
- `make_event(event_type, workflow_id, agent, subject_type, subject_id, payload, outcome="success") -> BaseEvent` - factory that auto-generates `event_id` (`evt_<uuid4hex[:8]>`) and ISO-8601 `timestamp`.
- `EventStore(backend: str = "memory", path: Optional[str] = None)` with:
  - `append(event: BaseEvent) -> None`
  - `all() -> List[BaseEvent]` (insertion order preserved)
  - `by_workflow(workflow_id: str) -> List[BaseEvent]`
  - `by_subject(subject_id: str) -> List[BaseEvent]`
  - `clear() -> None`
- `get_event_store()` / `reset_event_store()` module-level singleton accessors for the node + tests.

- [ ] Step 1: Write the failing test
- [ ] Step 2: Run test to verify it fails
- [ ] Step 3: Write minimal implementation
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Commit - `git commit -m "feat(memory): event taxonomy + append-only EventStore (Phase 5a.1)"`

---

### Task 5a.2: Memory Layer Contracts + Memory Policy Engine

**Files:**
- Create: `aiconnex_agent/memory/memory_layers.py`
- Create: `aiconnex_agent/memory/policy_engine.py`
- Test: `tests/test_memory_policy_engine.py`

**Memory layer contracts (`memory_layers.py`):**
- `SessionMemory` - `workflow_id`, `last_intent`, `steps_run: List[str]`, `status`, short-lived per-run snapshot.
- `EntityMemory` - `subject_id`, `subject_type`, `observations: List[Dict]` (accumulated facts about a dataset/model/asset).
- `ProceduralMemory` - `pattern: str`, `outcome: str`, `occurrences: int` (what worked/failed, recommended playbooks).
- `DecisionMemory` - `decision_id`, `question`, `answer`, `workflow_id` (HITL answers, overrides, approvals, branch choices).
- `MemoryBank` - aggregate holding `session: Dict[str, SessionMemory]`, `entities: Dict[str, EntityMemory]`, `procedures: List[ProceduralMemory]`, `decisions: List[DecisionMemory]`; `.to_context() -> Dict[str, Any]` serializer.

**Policy engine (`policy_engine.py`):**
- `RetentionDecision` - `action: Literal["retain_full", "retain_summary", "aggregate", "discard"]`, `target_layer: Optional[Literal["session","entity","procedural","decision"]]`.
- `MemoryPolicyEngine.decide(event: BaseEvent) -> RetentionDecision` - deterministic lookup table keyed on `event_type`:
  - `DatasetCompiled` -> retain_summary, entity
  - `ModelTrained` / `ModelEvaluated` -> retain_summary, entity
  - `ClarificationAnswered` -> retain_full, decision
  - `ClarificationRequested` -> discard (superseded by the answer)
  - `ConversationParsed` / `PlanCreated` -> retain_summary, session
  - `ArchiveUploaded` / `ArchiveDiscovered` / `ParserSelected` -> retain_summary, session
  - `outcome == "failure"` (any type) -> aggregate, procedural
  - unknown event_type -> discard (safe default; never crash)

- [ ] Step 1: Write the failing test
- [ ] Step 2: Run test to verify it fails
- [ ] Step 3: Write minimal implementation
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Commit - `git commit -m "feat(memory): 4-layer memory contracts + deterministic MemoryPolicyEngine (Phase 5a.2)"`

---

### Task 5a.3: Memory Builder (Deterministic Projection)

**Files:**
- Create: `aiconnex_agent/memory/memory_builder.py`
- Test: `tests/test_memory_builder.py`

**Interfaces:**
- `MemoryBuilder(policy: MemoryPolicyEngine)` with `build(events: List[BaseEvent]) -> MemoryBank` - pure projection: iterates events in order, asks the policy engine per event, and routes retained events into the correct layer of a fresh `MemoryBank`. `discard` decisions are skipped. `aggregate` decisions increment `ProceduralMemory.occurrences` for a matching `(pattern, outcome)` instead of appending duplicates.
- Idempotency guarantee: `build(events)` called twice on the same log yields structurally identical `MemoryBank`s (critical for replay in 5a.5).

- [ ] Step 1: Write the failing test
- [ ] Step 2: Run test to verify it fails
- [ ] Step 3: Write minimal implementation
- [ ] Step 4: Run test to verify it passes
- [ ] Step 5: Commit - `git commit -m "feat(memory): deterministic MemoryBuilder projecting events into 4 layers (Phase 5a.3)"`

---

### Task 5a.4: Memory Agent Node + LangGraph Wiring

**Files:**
- Create: `aiconnex_agent/memory/memory_agent.py`
- Modify: `aiconnex_agent/nodes/stub_nodes.py` (delegate `stub_memory_agent_node` -> `real_memory_agent_node`)
- Test: `tests/test_memory_agent_node.py`

**Interfaces:**
- `real_memory_agent_node(state: MasterAgentState) -> Dict[str, Any]`:
  - Derives `workflow_id` from `state.cuc.conversation.get("session_id")` or generates one; stashes it in `memory_context["workflow_id"]`.
  - **Write path** (intent in `{compile_zip, train_rul, detect_anomalies}` or any non-status intent): emits the relevant events into the `EventStore` from what the prior nodes populated - e.g. `DatasetCompiled` from `state.dic.compiled_dataset`/`dataset_identity`, `ModelTrained`/`ModelEvaluated` when platform ran, `PlanCreated` from `state.plan_steps`, `ClarificationAnswered` from `state.cuc.planning_hints["user_choice"]` if present.
  - **Read path** (intent `query_status`): does NOT emit new domain events; instead reads the current `MemoryBank`.
  - In both paths: runs `MemoryBuilder.build(store.all())` and writes `bank.to_context()` into `memory_context["memory_bank"]`, plus a `memory_context["last_saved_session"]` marker for backward-compat with the existing stub contract.
  - Returns `{"memory_context": <updated dict>, "active_agent": "evaluator"}`.

- [ ] Step 1: Write the failing test
- [ ] Step 2: Run test to verify it fails
- [ ] Step 3: Write minimal implementation
- [ ] Step 4: Run test to verify it passes + run FULL suite for zero regressions (check `test_stub_nodes.py::test_stub_memory_agent_node`)
- [ ] Step 5: Commit - `git commit -m "feat(memory): event-sourced Memory Agent node wired into LangGraph (Phase 5a.4)"`

---

### Task 5a.5: Replay & Rebuild

**Files:**
- Create: `aiconnex_agent/memory/replay.py`
- Test: `tests/test_memory_replay.py`

**Interfaces:**
- `rebuild_memory_from_events(events: List[BaseEvent], policy: Optional[MemoryPolicyEngine] = None) -> MemoryBank` - thin wrapper over `MemoryBuilder.build`, the canonical entry point for "rebuild memory from the log."
- `replay_workflow(store: EventStore, workflow_id: str) -> List[BaseEvent]` - returns the ordered event slice for one workflow (for "inspect why this memory fact exists").
- `explain_fact(store: EventStore, subject_id: str) -> List[BaseEvent]` - returns every event that contributed to an entity's memory (provenance/audit).

- [ ] Step 1: Write the failing test
- [ ] Step 2: Run test to verify it fails
- [ ] Step 3: Write minimal implementation
- [ ] Step 4: Run test to verify it passes + full suite green
- [ ] Step 5: Commit - `git commit -m "feat(memory): replay + provenance rebuild from event log (Phase 5a.5)"`

---

### Task 5a.6: mem0 Semantic Index Behind Entity Memory (SPRINT 2 - separate delivery)

> This task introduces the project's first memory-related LLM+network dependency. It is gated behind an adapter + deterministic local fake so Sprint 1 tests never require a live mem0 server. Do NOT start until 5a.1-5a.5 are merged and green.

**Files:**
- Create: `aiconnex_agent/memory/backends/__init__.py`
- Create: `aiconnex_agent/memory/backends/base.py` (`SemanticMemoryBackend` interface: `add(text, metadata)`, `search(query, limit) -> List[Dict]`)
- Create: `aiconnex_agent/memory/backends/local_fake.py` (in-memory substring/keyword match implementing the interface - zero LLM/network, for tests)
- Create: `aiconnex_agent/memory/backends/mem0_adapter.py` (wraps `mem0ai` client; used only when `AICONNEX_MEMORY_BACKEND=mem0`)
- Modify: `aiconnex_agent/memory/memory_builder.py` (after materializing Entity memory, mirror entity observations into the configured `SemanticMemoryBackend`)
- Modify: `aiconnex_agent/memory/memory_agent.py` (read path for `query_status` consults the semantic backend for fuzzy cross-session recall, falling back to deterministic entity lookup)
- Test: `tests/test_memory_semantic_backend.py`

**Design guardrails (decided in planning):**
- mem0 sits BEHIND the Entity memory layer only. Decision memory and Procedural memory stay 100% deterministic/auditable - "why did the system choose this branch" must never depend on non-deterministic LLM extraction.
- Backend selected via `AICONNEX_MEMORY_BACKEND` env (`local_fake` default, `mem0` opt-in), mirroring the intended `AICONNEX_LLM_BACKEND` Ollama->OpenAI switch.
- All Sprint 1 tests continue to run against `local_fake` - no live mem0 subprocess in CI.

- [ ] Step 1: Write the failing test
- [ ] Step 2: Run test to verify it fails
- [ ] Step 3: Write minimal implementation (interface + local fake first; mem0_adapter guarded import last)
- [ ] Step 4: Run test to verify it passes with `local_fake`; full suite green with mem0 NOT installed
- [ ] Step 5: Commit - `git commit -m "feat(memory): mem0 semantic index behind Entity memory with local fake fallback (Phase 5a.6)"`

---

## Plan Self-Review

1. **Spec Coverage:** All five user-requested Sprint 1 additions are covered - (1) 4 memory layers = Task 5a.2/5a.3; (2) event taxonomy = 5a.1; (3) Memory Policy Engine = 5a.2; (4) memory assets not just search = the 4 typed layer products in 5a.2/5a.3; (5) replayability = 5a.5. Sprint 2 mem0 = 5a.6.
2. **Placeholder Scan:** No TBD/TODO. Every module has a concrete interface and test intent.
3. **Type Consistency:** `MasterAgentState.memory_context` stays `Dict[str, Any]` - `MemoryBank.to_context()` serializes into it; no state migration.
4. **Zero-LLM Invariant:** Sprint 1 (5a.1-5a.5) has no LLM/network. Only 5a.6 introduces mem0, gated behind an adapter + local fake so tests stay offline/deterministic - consistent with the repo's `AICONNEX_DISABLE_LLM` precedent.
5. **Non-regression:** `graph.py` untouched (delegation pattern). Only `stub_nodes.py::stub_memory_agent_node` changes; `test_stub_nodes.py::test_stub_memory_agent_node` preserved by keeping the `last_saved_session` key.
6. **Ordering rationale:** Memory built first among agents not because it's smallest (it isn't - it's ~7 modules) but because Scout/Platform/Planner will all emit into this event log; fixing the taxonomy now avoids retrofitting event emission later.

---

## Execution Choice

Sprint 1 (5a.1-5a.5) executed inline in this session. Sprint 2 (5a.6) deferred until Sprint 1 is merged and confirmed stable.
