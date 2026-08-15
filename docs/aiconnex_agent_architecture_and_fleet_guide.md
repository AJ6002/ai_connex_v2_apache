# AIConnex — Master Agent Architecture & Fleet Placement Guide

> **Branch:** `be`  
> **Framework:** LangGraph `StateGraph` compiled state machine (`aiconnex_agent/graph.py`)  
> **Persistence:** SQLite Checkpointer (`SqliteSaver` at `chatbot/backend/data/sessions/agent_checkpoints.sqlite`)  
> **Total Agents / Nodes:** 23 Total Agents across 22 Compiled LangGraph Nodes and 5 Operational Phases

---

## 1. Executive Summary & Graph Topology

AIConnex utilizes a **22-node compiled LangGraph `StateGraph`** that operates as an event-driven pipeline. All state is centralized in a single typed model — `MasterAgentState` (`aiconnex_agent/state.py`) — which accumulates **12 distinct manifest contracts** across execution.

### Complete 22-Node Graph Visual Topology

```text
START
  │
  ▼
[conversation_parser_node] ──► [intent_extraction_node] ──► [contract_manager_node]
  ▲                                                                 │
  │                                                                 ▼
  │                                                    [conversation_planner_node]
  │                                                       /                  \
  │                                     [action ≠ recommend_upload]   [action = recommend_upload]
  │                                               │                            │
  └───────────── [response_writer_node] ◄─────────┘                   [upload_gate_node]
                     (interrupt)                                         (interrupt)
                                                                            │
                                                            ┌───────────────┘
                                                            │ (resume upload_path)
                                                            ▼
                                                [archive_discovery_node]
                                                            │
                                                [structure_analysis_node]
                                                            │
                                                [entity_analysis_node]
                                                            │
                                             [relationship_analysis_node]
                                                            │
                                                [temporal_analysis_node]
                                                            │
                                                [feature_analysis_node]
                                                            │
                                                [quality_analysis_node]
                                                            │
                                              [statistical_analysis_node]
                                                            │
                                             [exploration_synthesizer_node]
                                                            │
                                                       [hitl_node] ◄─── (interrupt loop)
                                                            │
                                                   [pipeline_lock_node]
                                                            │
                                                  [workflow_planner_node]
                                                            │
                                                   [platform_agent_node]
                                                            │
                                                    [memory_agent_node]
                                                            │
                                                           END
```

---

## 2. Comprehensive Agent Inventory & Placement

### Phase 1: Intake & Pre-Upload Conversational Agents (6 Nodes)

These agents handle natural-language chat interaction with the user to build the **Conversation Understanding Contract (CUC)** before any file is uploaded.

| Agent Name | LangGraph Node | File Location | Graph Placement | Input Artifact | Output Artifact |
|---|---|---|---|---|---|
| **Conversation Manager Agent** | `conversation_parser_node` | `aiconnex_agent/parser/conversation_parser.py` | `START → conversation_parser_node` | Raw user chat text | `state.messages`, normalized thread ID |
| **Intent Extraction Agent** | `intent_extraction_node` | `aiconnex_agent/parser/semantic_extractor.py` | `conversation_parser_node → intent_extraction_node` | `state.messages` | `state.latest_extraction` (`primary_intent`, `task_family`, `target_column`) |
| **Contract Manager Agent** | `contract_manager_node` | `aiconnex_agent/parser/contract_manager.py` | `intent_extraction_node → contract_manager_node` | `state.latest_extraction` | `state.cuc` (Conversation Understanding Contract) |
| **Conversation Planner Agent** | `conversation_planner_node` | `aiconnex_agent/parser/conversation_planner.py` | `contract_manager_node → conversation_planner_node` | `state.cuc`, `required_fields.yaml` rules | `state.conversation_plan` (`action`), `state.upload_readiness` |
| **Response Writer Agent** | `response_writer_node` | `aiconnex_agent/parser/response_writer.py` | `conversation_planner_node (ask/summarize) → response_writer_node` | `state.conversation_plan`, `state.cuc` | `state.response_text`, chat SSE events |
| **Upload Gate Agent** | `upload_gate_node` | `aiconnex_agent/graph.py:94-140` | `conversation_planner_node (upload) → upload_gate_node` | Complete CUC manifest | `state.upload_path` (on upload resume) |

---

### Phase 2: Scout Dataset Profiling & Deep Analysis Agents (9 Nodes)

Once a dataset file is posted to `/api/upload`, the graph resumes into a linear 9-node Scout chain that inspects, profiles, and analyzes the data with **zero domain hardcoding**.

| Agent Name | LangGraph Node | File Location | Graph Placement | Input Artifact | Output Artifact |
|---|---|---|---|---|---|
| **Archive Discovery Agent** | `archive_discovery_node` | `aiconnex_agent/scout/nodes/archive_discovery.py` | `upload_gate_node → archive_discovery_node` | `state.upload_path` | `state.archive_manifest` (format, file tree, strategy peek) |
| **Structure Analysis Agent** | `structure_analysis_node` | `aiconnex_agent/scout/nodes/structure_analysis.py` | `archive_discovery_node → structure_analysis_node` | `state.archive_manifest` | `state.structure_analysis` (compiled CSV path, dtypes, row/col counts) |
| **Entity Analysis Agent** | `entity_analysis_node` | `aiconnex_agent/scout/nodes/entity_analysis.py` | `structure_analysis_node → entity_analysis_node` | `state.structure_analysis` | `state.entity_inventory` (column roles: ID, timestamp, feature, target) |
| **Relationship Analysis Agent** | `relationship_analysis_node` | `aiconnex_agent/scout/nodes/relationship_analysis.py` | `entity_analysis_node → relationship_analysis_node` | `state.entity_inventory` | `state.relationship_graph` (FK keys, join paths across tables) |
| **Temporal Analysis Agent** | `temporal_analysis_node` | `aiconnex_agent/scout/nodes/temporal_analysis.py` | `relationship_analysis_node → temporal_analysis_node` | `state.structure_analysis`, `state.entity_inventory` | `state.temporal_structure` (frequency, monotonicity, time gaps, seasonality) |
| **Feature Analysis Agent** | `feature_analysis_node` | `aiconnex_agent/scout/nodes/feature_analysis.py` | `temporal_analysis_node → feature_analysis_node` | `state.entity_inventory`, `state.temporal_structure` | `state.feature_catalog_v2` (lags, rolling means, >0.95 correlation drops) |
| **Quality Assessment Agent** | `quality_analysis_node` | `aiconnex_agent/scout/nodes/quality_analysis.py` | `feature_analysis_node → quality_analysis_node` | `state.structure_analysis` | `state.quality_assessment` (quality score, issue list) |
| **Statistical Analysis Agent** | `statistical_analysis_node` | `aiconnex_agent/scout/nodes/statistical_analysis.py` | `quality_analysis_node → statistical_analysis_node` | `state.structure_analysis`, `state.entity_inventory` | `state.statistical_profile` (mean, std, percentiles, skewness, kurtosis) |
| **Exploration Synthesizer Agent** | `exploration_synthesizer_node` | `aiconnex_agent/scout/nodes/exploration_synthesizer.py` | `statistical_analysis_node → exploration_synthesizer_node` | All 8 prior Scout manifests | `state.dataset_exploration_manifest`, `state.dic` (`AnalyticalRecipe[]`) |

---

### Phase 3: Governance, HITL & Workflow Planning Agents (3 Nodes)

These agents manage human recipe selection, freeze the decision as an immutable audit lock, and construct the execution DAG.

| Agent Name | LangGraph Node | File Location | Graph Placement | Input Artifact | Output Artifact |
|---|---|---|---|---|---|
| **Human-In-The-Loop (HITL) Agent** | `hitl_node` | `aiconnex_agent/planning/hitl_node.py` & `hitl_flow.py` | `exploration_synthesizer_node → hitl_node` | `state.dic` (`recipes`) | `state.hitl_contract` (selected recipe ID, e.g. `R001`, target, preferences) |
| **Pipeline Lock Agent** | `pipeline_lock_node` | `aiconnex_agent/planning/pipeline_lock.py` | `hitl_node → pipeline_lock_node` | `state.hitl_contract` | `state.pipeline_lock` (`PipelineLockManifest` immutable freeze) |
| **Workflow Planner Agent** | `workflow_planner_node` | `aiconnex_agent/planning/workflow_planner.py` | `pipeline_lock_node → workflow_planner_node` | `state.pipeline_lock` | `state.workflow_manifest` (3-stage DAG: `feature_engineering` → `train` → `evaluate`) |

---

### Phase 4: Platform Execution & Evaluation Triad Agents (4 Agents)

These agents execute parallel model training, quantitative scoring, qualitative safety evaluation, and MCDA winner selection.

| Agent Name | LangGraph Node / Module | File Location | Graph Placement | Input Artifact | Output Artifact |
|---|---|---|---|---|---|
| **Platform Agent** | `platform_agent_node` | `aiconnex_agent/platform/platform_node.py` | `workflow_planner_node → platform_agent_node` | `state.dic`, `state.pipeline_lock`, compiled CSV | `state.candidate_recipes`, `state.oof_predictions` |
| **Scorer Agent** | Sub-agent / Helper | `aiconnex_agent/platform/scorer_agent.py` | Executed inside `platform_agent_node` | `y_true`, `y_pred`, latency | `state.scorer_reports` (`ScorerReport`: RMSE, R², MAE, size) |
| **Judge Agent** | Sub-agent / Helper | `aiconnex_agent/platform/judge_agent.py` | Executed inside `platform_agent_node` | `ScorerReport`, dataset summary | `state.judge_reports` (`JudgeReport`: risk score, domain safety) |
| **Selector Agent** | Sub-agent / Helper | `aiconnex_agent/platform/selector_agent.py` | Executed inside `platform_agent_node` | `scorer_reports`, `judge_reports`, CUC intent | `state.selection_result` (`SelectionResult` winning model) |

---

### Phase 5: Audit & Memory Agents (1 Node)

Persists complete session snapshots into the event-sourced audit store.

| Agent Name | LangGraph Node | File Location | Graph Placement | Input Artifact | Output Artifact |
|---|---|---|---|---|---|
| **Memory Agent** | `memory_agent_node` | `aiconnex_agent/memory/memory_agent.py` | `platform_agent_node → memory_agent_node → END` | Entire `MasterAgentState` | `state.memory_context`, audit logs in `session_store.db` |

---

## 3. State Contracts Observability Map

All **12 accumulative manifest contracts** across all 23 agents are inspectable in real-time via the read-back API:

```http
GET /api/agent/state?session_id=<session_id>
```

```json
{
  "session_id": "ag_session_12345",
  "cuc": { "goal": { "primary_intent": "train_rul", "task_family": "regression" } },
  "conversation_plan": { "action": "recommend_upload" },
  "upload_readiness": { "ready": true, "missing_fields": [] },
  "archive_manifest": { "archive_type": "zip", "total_files": 4 },
  "structure_analysis": { "compiled_csv_path": "scratch/scout_output/compiled.csv" },
  "entity_inventory": { "roles": { "unit_number": "entity_id", "time_in_cycles": "timestamp" } },
  "relationship_graph": { "is_multi_table": false },
  "temporal_structure": { "is_time_series": true, "frequency": "per_cycle" },
  "feature_catalog_v2": { "derived_candidates": ["lag_sensor_2", "rolling_mean_sensor_11"] },
  "quality_assessment": { "quality_score": 94.5, "passed": true },
  "statistical_profile": { "column_stats": { ... } },
  "dataset_exploration_manifest": { "recipes": [ { "id": "R001", "title": "RUL Regression" } ] },
  "hitl_contract": { "selected_recipe_id": "R001", "hitl_complete": true },
  "pipeline_lock": { "locked_recipe_id": "R001", "locked_at": "2026-08-13T18:54:00Z" },
  "workflow_manifest": { "stages": [ "feature_engineering", "train", "evaluate" ] },
  "active_agent": "memory",
  "confidence_score": 0.95
}
```
