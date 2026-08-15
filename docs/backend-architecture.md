# AIConnex Backend — Architecture Reference

> Branch: `be`  
> Last updated: reflects Tasks 1–15 (generalized HITL, 8-node Scout, Pipeline Lock, Workflow Planner, HITL node, full graph wiring, E2E verification).

---

## 1. Overview

The backend is a **Flask API** (`chatbot/backend/app.py`) that serves as a thin HTTP layer over a compiled **LangGraph StateGraph** (`aiconnex_agent/graph.py`). All business logic, sequencing, and state lives in the graph. Flask's job is to start graph threads, stream SSE events to the frontend, handle file uploads, and expose state for inspection.

The graph is a **22-node, event-sourced pipeline** split cleanly into two phases:

| Phase | Trigger | Nodes | What happens |
|---|---|---|---|
| Pre-Upload | User sends a chat message | 6 nodes | Natural-language conversation to build a CUC (Conversation Understanding Contract) |
| Post-Upload | User uploads a dataset file | 16 nodes | Deep dataset analysis → HITL recipe selection → plan lock → training |

There is exactly one `MasterAgentState` per session thread. Every node reads from it and writes typed artifacts back to it. The state is persisted across requests by a SQLite checkpointer (`SqliteSaver`), with an in-memory fallback when the sqlite package isn't installed.

---

## 2. Entry Points (Flask Routes)

| Route | Method | Purpose |
|---|---|---|
| `POST /api/agent/chat` | `POST` | Start or continue a pre-upload chat conversation. Streams SSE events back. Auto-detects whether the thread is paused (interrupted) and routes to resume vs. new-turn path. |
| `POST /api/agent/seed` | `POST` | Scripted bypass: seed a fully-formed CUC directly (Postman / test harness). Skips the NLP conversation. Auto-resumes through the `summarize` interrupt and parks the graph at `upload_gate_node`. |
| `POST /api/agent/resume` | `POST` | Resume any paused HITL interrupt with an explicit answer. Streams SSE events. |
| `GET /api/agent/state` | `GET` | Read-only state inspection. Returns every manifest accumulated on the checkpoint for a given `session_id`. |
| `POST /api/upload` | `POST` | Multipart file upload. Saves the file, then resumes the parked `upload_gate_node` thread with the file path — which drives the graph into the Scout chain. |
| `GET /api/health` | `GET` | Liveness check. |

### SSE event schema

All streaming routes emit newline-delimited SSE frames:

```
data: {"type": "text",      "delta": "...", "node": "response_writer_node"}
data: {"type": "interrupt",  "payload": {...}, "session_id": "ag_xxx"}
data: {"type": "compiled",   "compiled_csv_path": "..."}
data: {"type": "done",       "session_id": "ag_xxx"}
data: {"type": "error",      "message": "..."}
```

---

## 3. Graph Topology

```
START
  │
  ▼
conversation_parser_node ──► intent_extraction_node ──► contract_manager_node
  ▲                                                              │
  │                                                              ▼
  │                                               conversation_planner_node
  │                                                  /                    \
  │                                [action≠recommend_upload]   [action=recommend_upload]
  │                                          │                            │
  └──────── response_writer_node ◄───────────┘               upload_gate_node
              (interrupt/resume)                              (interrupt/resume)
                                                                    │
                                                    ┌───────────────┘
                                                    │  resume(upload_path)
                                                    ▼
                                        archive_discovery_node
                                                    │
                                        structure_analysis_node
                                                    │
                                         entity_analysis_node
                                                    │
                                      relationship_analysis_node
                                                    │
                                        temporal_analysis_node
                                                    │
                                        feature_analysis_node
                                                    │
                                        quality_analysis_node
                                                    │
                                      statistical_analysis_node
                                                    │
                                     exploration_synthesizer_node
                                                    │
                                               hitl_node  ◄──── (interrupt/resume loop)
                                                    │
                                        pipeline_lock_node
                                                    │
                                       workflow_planner_node
                                                    │
                                        platform_agent_node
                                                    │
                                        memory_agent_node
                                                    │
                                                   END
```

The only **conditional edge** in the live graph is `route_after_planner`, which reads `ConversationPlan.action` to choose between `response_writer_node` and `upload_gate_node`. Everything else is a linear `add_edge`.

---

## 4. Shared State — `MasterAgentState`

Defined in `aiconnex_agent/state.py`. A single Pydantic model that accumulates artifacts from every node. The checkpointer serialises and deserialises this model between requests.

### Pre-Upload fields

| Field | Type | Written by | Purpose |
|---|---|---|---|
| `session_id` | `str` | constructor | Stable session key, never mutated |
| `messages` | `List[Dict]` | conversation_parser_node | Full chat history |
| `cuc` | `ConversationUnderstandingContract` | contract_manager_node | Accumulated intent across all turns |
| `latest_extraction` | `Dict` | intent_extraction_node | Transient handoff this turn (overwritten each turn) |
| `conversation_plan` | `ConversationPlan` | conversation_planner_node | Current turn decision (ask/summarize/confirm/recommend_upload) |
| `upload_readiness` | `UploadReadinessContract` | conversation_planner_node | Formal exit artifact when intent is ready |
| `response_text` | `str` | response_writer_node | Natural-language text for the current turn |
| `upload_path` | `str` | upload_gate_node (on resume) | Filesystem path to the uploaded file |
| `confidence_score` | `float` | intent_extraction_node | Overall extraction confidence |

### Scout 9-node split fields

| Field | Type | Written by |
|---|---|---|
| `archive_manifest` | `ArchiveManifest` | archive_discovery_node |
| `structure_analysis` | `StructureAnalysis` | structure_analysis_node |
| `entity_inventory` | `EntityInventory` | entity_analysis_node |
| `relationship_graph` | `RelationshipGraph` | relationship_analysis_node |
| `temporal_structure` | `TemporalStructure` | temporal_analysis_node |
| `feature_catalog_v2` | `FeatureCatalogV2` | feature_analysis_node |
| `quality_assessment` | `QualityAssessment` | quality_analysis_node |
| `statistical_profile` | `StatisticalProfile` | statistical_analysis_node |
| `dataset_exploration_manifest` | `DatasetExplorationManifest` | exploration_synthesizer_node |

### Planning phase fields

| Field | Type | Written by | Immutable? |
|---|---|---|---|
| `hitl_contract` | `HITLContract` (as `Any`) | hitl_node | No — accumulates across HITL turns |
| `pipeline_lock` | `PipelineLockManifest` | pipeline_lock_node | Yes — node is idempotent, never re-locks |
| `workflow_manifest` | `WorkflowManifest` | workflow_planner_node | No — regeneratable from pipeline_lock |

### Legacy / downstream fields

`dic` (`DatasetIntelligenceContract`), `scout_enriched`, `pre_compiler`, `candidate_recipes`, `scorer_reports`, `judge_reports`, `selection_result` — populated by platform/memory nodes or carried for backward compatibility.

---

## 5. Pre-Upload Phase — Node Detail

The pre-upload chain converts a raw user message into a fully-resolved `ConversationUnderstandingContract` before any file is accepted.

### conversation_parser_node
> Registered name: `"conversation_parser_node"` — maps to `conversation_manager_node`. The name is preserved because `/api/agent/seed` seeds state `as_node="conversation_parser_node"`.

Normalises the incoming message, sets `session_id`, prepares the message list for downstream extraction.

### intent_extraction_node
Calls `SemanticExtractor` with the current message + history. Uses the LLM (OpenRouter / Ollama) to pull structured fields from the user's words — `primary_intent`, `task_family`, `target column`, `business_context`, etc. On LLM failure, heuristic fallback runs. Writes to `state.latest_extraction` (not directly to `state.cuc` — that's the contract manager's job).

### contract_manager_node
The **merge layer**. Reads `state.latest_extraction` and folds it into `state.cuc` turn-by-turn:
- Fields not mentioned this turn are left untouched.
- Contradictions (same field, different value) are recorded as `ContradictionRecord` objects rather than silently overwriting.
- Goal fields `primary_intent` and `task_family` are the only ones contradiction-checked (free-text fields like `business_goal` always take the newest value).

### conversation_planner_node
The **decision engine**. Reads the registry-defined required-fields list and the current `state.cuc`, then emits one `ConversationPlan.action`:

1. `confirm` — unresolved contradiction exists
2. `ask` — required fields still missing (one per turn)
3. `summarize` — all fields satisfied but first time, so recap before upload (registry-controlled)
4. `recommend_upload` — satisfied + already summarised → ready

Also produces `UploadReadinessContract` every turn for observability.

### response_writer_node
Renders the planner's decision into natural-language text using the LLM, then calls `interrupt()` to park the graph and await the user's next message. On resume, execution loops back to `conversation_parser_node`.

### upload_gate_node
Parks the graph with `interrupt_type="advise_upload"`. On resume, `/api/upload` passes the saved file path as the resume value. The node writes `upload_path` to state and execution advances into Scout.

---

## 6. Post-Upload Phase — Scout 9 Nodes

All Scout nodes live in `aiconnex_agent/scout/nodes/`. They form a strict linear chain — each node reads earlier nodes' artifacts from state and adds its own typed manifest.

### Node 1 — archive_discovery_node
`state.upload_path` → `state.archive_manifest`

Pure filesystem inspection. No data parsing. Detects archive type (zip / single file / folder), walks the tree recursively, fingerprints each file's format, builds a parser candidate map, hashes the archive for reproducibility. Runs `strategy_peek` to detect multi-strategy compilation choices (e.g. NASA C-MAPSS: "unified all conditions" vs "separate per condition") and emits a `strategy_choice` interrupt when genuine ambiguity exists.

### Node 2 — structure_analysis_node
`state.archive_manifest` → `state.structure_analysis`

Passes the archive through the `UnifiedCompiler` (via `compiler_adapter.py`). Produces a compiled CSV on disk, catalogues per-source-file schemas (column names + dtypes + row counts), and records the `compiled_csv_path` that all downstream analysis nodes read from.

### Node 3 — entity_analysis_node
`state.structure_analysis` → `state.entity_inventory`

Classifies every column by role: `entity_id | timestamp | measurement | dimension | target_candidate | metadata | unknown`. Result drives entity-aware feature engineering and target selection in later nodes.

### Node 4 — relationship_analysis_node
`state.entity_inventory` → `state.relationship_graph`

For multi-file uploads: detects join keys, FK candidates, and entity links via value-overlap scoring. Single-file uploads produce an empty graph (`is_multi_table=False`) — no false relationships.

### Node 5 — temporal_analysis_node
`state.structure_analysis`, `state.entity_inventory` → `state.temporal_structure`

Detects whether the dataset is time-series: finds timestamp columns, infers sampling frequency (`daily`, `hourly`, `per_cycle`, `irregular`), checks monotonicity and gap presence, extracts date range and seasonality hints. Sets `is_time_series=False` cleanly for purely tabular data.

### Node 6 — feature_analysis_node
`state.entity_inventory`, `state.temporal_structure` → `state.feature_catalog_v2`

Produces a feature-level catalog with category tags (`raw | derived | lagged | rolling | encoded`), role tags, and derived feature candidates (lag, rolling mean, diff, ratio, interaction). Also flags highly-correlated column pairs (`>= 0.95`) as redundant.

### Node 7 — quality_analysis_node
`state.structure_analysis` → `state.quality_assessment`

Scans for null percentages per column, duplicate rows, outlier signals, constant/zero-variance columns, and class imbalance. Issues are classified by severity (`info | warning | error`). A `passed=False` result means at least one error-severity issue exists.

### Node 8 — statistical_analysis_node
`state.structure_analysis`, `state.entity_inventory` → `state.statistical_profile`

Computes per-column descriptive stats (mean, std, min, max, p25/p75/p95, skewness, kurtosis) and pairwise correlation pairs above a configurable threshold. Result is the quantitative foundation the synthesizer's recipe confidence scores are built from.

### Node 9 — exploration_synthesizer_node
All 8 prior state fields → `state.dataset_exploration_manifest` + `state.dic`

The **combiner and recipe generator**. Reads every prior manifest, constructs the master `DatasetExplorationManifest`, and derives the `AnalyticalRecipe` catalog — the list of candidate ML objectives the user picks from at HITL. Recipe titles, task types, target columns, and confidence scores are all derived from the data (business_context from CUC + entity/temporal/quality analysis). Nothing is hardcoded per domain. Also writes `state.dic` (legacy `DatasetIntelligenceContract`) for backward compatibility with the Platform Agent and Memory node.

---

## 7. HITL Phase

### hitl_node
`state.dic` → `state.hitl_contract`

A real LangGraph node using multiple `interrupt()`/`resume()` calls within a single node body. Flow:

1. First entry: builds the recipe-catalog opening message from the real DIC (dynamic dataset name + recipe list). Calls `interrupt()` with `interrupt_type="clarification"`.
2. On each resume: calls `process_hitl_turn(user_answer, contract, dic_context)` which runs LLM extraction + merge + `apply_recipe_context`. The LLM prompt is constructed entirely from Scout's output — no hardcoded domain vocabulary.
3. Loop continues until `contract.hitl_complete=True` (recipe picked with confidence). Capped at 20 turns.
4. Exits with the finalised `HITLContract` written to state.

**Recipe resolution strategies** (in fallback order when LLM JSON parsing fails):
- Numeric index (`"1"`, `"2"`)
- Letter (`"A"`, `"B"`)
- Recipe ID (`"R001"`)
- Title fuzzy match (≥ 2 salient words overlap)

### HITL data flow

```
state.dic.recipes  ──►  build_hitl_system_prompt()  ──►  LLM  ──►  HITLTurnExtraction
                                                                           │
                                                                     _merge()
                                                                           │
                                                               HITLContract (accumulated)
                                                                           │
                                                                apply_recipe_context()
                                                                           │
                                                             target_column, task_family
                                                             derived from picked recipe
```

---

## 8. Planning Phase

### pipeline_lock_node
`state.hitl_contract` → `state.pipeline_lock`

Freezes the user's decision as an immutable `PipelineLockManifest`. This is the **audit boundary** — downstream nodes read from `pipeline_lock`, they never touch `hitl_contract` directly. Idempotent: if `state.pipeline_lock` is already set, the node is a no-op. Refuses to lock if `hitl_complete=False`.

Lock manifest fields: `session_id`, `locked_recipe_id`, `business_objective`, `selected_workflow_type`, `target_column`, `operational_preferences`, `success_metrics`, `locked_at`, `locked_by`, `hitl_turn_count`.

### workflow_planner_node
`state.pipeline_lock` → `state.workflow_manifest`

Converts the locked recipe into a concrete `WorkflowManifest` with typed `WorkflowStage` nodes and DAG-ready `depends_on` edges. v1 always produces a linear 3-stage plan:

| stage_id | task | depends_on |
|---|---|---|
| stage_1 | `feature_engineering` | `[]` |
| stage_2 | `train` or `detect_anomalies` | `["stage_1"]` |
| stage_3 | `evaluate` | `["stage_2"]` |

Unknown task families produce a single-stage safe fallback with an explicit warning, never a silent misroute. The schema supports compound multi-branch plans (v2).

---

## 9. Terminal Phase

### platform_agent_node
Reads `state.dic` and `state.pipeline_lock`. Runs the Platform Harness — trains candidate models against the compiled dataset, runs the Scorer/Judge triad, and selects a winner via MCDA. Writes `selection_result`, `scorer_reports`, `judge_reports`.

### memory_agent_node
Writes the finalised session context (CUC + DIC + selection result + workflow manifest) to the event-sourced memory audit log, keyed by `state.session_id`. Produces `memory_context` for downstream retrieval.

---

## 10. Contract Pipeline

The 5 canonical contracts that flow through the system, in order:

```
[User chat]
    │
    ▼
ConversationUnderstandingContract (CUC)
    — goal, observed, inferred, business_context, constraints,
      dataset_expectation, clarifications_required, contradictions
    │
    ▼  (file upload)
ScoutEnrichedContract
    — CUC + upload metadata + archive discovery + parser selection
    │
    ▼  (UnifiedCompiler)
PreCompilerContract
    — ScoutEnriched + CompilerRequest
    │
    ▼
DatasetIntelligenceContract (DIC)
    — compiled dataset summary, schema_map, statistics, quality_report,
      derived_features, problem_candidates, target_candidates,
      feature_catalog, recipes (AnalyticalRecipe[])
    │
    ▼  (HITL)
PipelineLockManifest
    — locked_recipe_id, business_objective, selected_workflow_type,
      target_column, operational_preferences, success_metrics, locked_at
    │
    ▼
WorkflowManifest
    — stages (WorkflowStage[]), total_stages, depends_on edges
```

---

## 11. State Observability — GET /api/agent/state

Every manifest on the checkpoint is surfaced by the state endpoint:

```json
{
  "session_id": "ag_abc123",

  "cuc": { ... },
  "conversation_plan": { "action": "recommend_upload" },
  "upload_readiness": { "ready": true, "missing_fields": [] },
  "manifest_ready": true,

  "archive_manifest": { ... },
  "structure_analysis": { ... },
  "entity_inventory": { ... },
  "relationship_graph": { ... },
  "temporal_structure": { ... },
  "feature_catalog_v2": { ... },
  "quality_assessment": { ... },
  "statistical_profile": { ... },
  "dataset_exploration_manifest": { ... },

  "hitl_contract": { ... },
  "pipeline_lock": { ... },
  "workflow_manifest": { ... },

  "active_agent": "platform",
  "confidence_score": 0.95,
  "next_nodes": []
}
```

---

## 12. Checkpointing

`aiconnex_agent/graph.py` compiles the graph with a checkpointer:

- **Primary**: `SqliteSaver` at `chatbot/backend/data/sessions/agent_checkpoints.sqlite` — threads survive Flask auto-reloads and cross-request state is preserved.
- **Fallback**: `MemorySaver` when `langgraph-checkpoint-sqlite` isn't installed — state is in-process only.

The checkpointer is constructed with `check_same_thread=False` because Flask serves concurrent requests from multiple worker threads that all share the one compiled graph singleton.

---

## 13. File Map

```
aiconnex_agent/
├── graph.py                   # StateGraph topology — all 22 nodes + edges
├── state.py                   # MasterAgentState — single source of truth
├── schemas.py                 # All Pydantic contracts (CUC → DIC → Planning)
├── runner.py                  # execute_and_stream / resume_with_user_input
├── parser/
│   ├── conversation_parser.py # conversation_manager_node (entry)
│   ├── semantic_extractor.py  # LLM + heuristic field extraction
│   ├── contract_manager.py    # CUC merge + contradiction detection
│   ├── conversation_planner.py# Decision engine (ask/summarize/recommend_upload)
│   ├── response_writer.py     # LLM text render + interrupt/resume
│   ├── cuc_completion.py      # is_manifest_minimally_complete()
│   └── ...
├── scout/
│   ├── nodes/
│   │   ├── archive_discovery.py
│   │   ├── structure_analysis.py
│   │   ├── entity_analysis.py
│   │   ├── relationship_analysis.py
│   │   ├── temporal_analysis.py
│   │   ├── feature_analysis.py
│   │   ├── quality_analysis.py
│   │   ├── statistical_analysis.py
│   │   └── exploration_synthesizer.py
│   ├── compiler_adapter.py    # UnifiedCompiler integration
│   ├── recipe_catalog_builder.py
│   └── strategy_peek.py       # Multi-strategy interrupt logic
└── planning/
    ├── hitl_node.py            # Multi-interrupt HITL loop
    ├── pipeline_lock.py        # Immutable decision freeze
    └── workflow_planner.py     # WorkflowManifest builder

chatbot/backend/
├── app.py                     # Flask routes + SSE streaming
├── hitl_schemas.py            # HITLContract, HITLTurnExtraction
├── hitl_extraction.py         # build_hitl_system_prompt, extract_hitl_turn
└── hitl_flow.py               # process_hitl_turn (extract → merge → derive)
```

---

## 14. Design Decisions

| Decision | What was chosen | What was rejected |
|---|---|---|
| Scout granularity | 8 real analysis nodes, each with a typed state field | Single fast-pass scout (would reuse ETP-specific compiler assumptions) |
| HITL interaction pattern | Multiple `interrupt()` calls within one node body | Graph self-loop (more complex state passing across edges) |
| HITL prompt generation | `build_hitl_system_prompt(dic_context)` — fully dynamic from Scout output | Hardcoded `_HITL_SYSTEM_PROMPT` (leaked ETP vocabulary for any dataset) |
| Pipeline audit boundary | `pipeline_lock` immutable after first write | Mutable HITL contract driving platform agent directly |
| `workflow_manifest` in v1 | Descriptive / audit artifact, not driving Platform Agent | Driving Platform Agent from `workflow_manifest.stages` (deferred to v2) |
| `state.hitl_contract` type | `Optional[Any]` | `Optional[HITLContract]` — `HITLContract` lives in `chatbot/backend` which is not on the `aiconnex_agent` import path at state-definition time |
| SqliteSaver import | Lazy inside `build_graph()` try/except | Module-level import (would crash the entire package if the sqlite package wasn't installed, defeating the MemorySaver fallback) |
