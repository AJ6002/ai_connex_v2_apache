# Phase 4: Planning Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the real `Planning Engine` node replacing `stub_planning_engine_node`. It takes the validated `ConversationUnderstandingContract` (CUC) produced by Phase 3's Conversation Parser and deterministically routes it into an `ExecutionPlan` of `TaskStep`s targeting the correct downstream agent (`scout` | `platform` | `memory`).

**Architecture:** Two sub-modules, mirroring the Phase 3 parser pattern for isolation and testability:
`IntentPlanMapper` (pure intent → plan-template lookup table, zero I/O) → `PlanValidator` (Pydantic-validates the raw step dicts into a strongly-typed `ExecutionPlan`, with a safe single-step fallback if validation fails or the mapper returns nothing). The orchestrator `real_planning_engine_node` wires both together and is delegated to from `stub_planning_engine_node`, exactly as `real_conversation_parser_node` is delegated to from `stub_conversation_parser_node` — so `graph.py` topology and edge functions (`route_agent`, `route_after_evaluator`) require **zero changes**.

**Why deterministic (no LLM here):** Routing "which agent handles which task" is a fixed, auditable business rule (`compile_zip` → scout, `train_rul` → scout+platform, `query_status` → memory, etc.), not a judgment call requiring language understanding. Keeping it deterministic means it is 100% unit-testable in isolation with zero network/LLM dependency, consistent with the project's "never build a component you can't immediately test in isolation" principle. This is the same rationale `SemanticExtractor` already uses for its default heuristic fallback path.

**Tech Stack:** Python 3.10+, `pydantic`, `pytest`. No new dependencies.

## Global Constraints
- Sub-module isolation: `IntentPlanMapper` and `PlanValidator` each live in `aiconnex_agent/planning/` with one responsibility, same layout convention as `aiconnex_agent/parser/`.
- Zero LLM calls, zero I/O, zero network calls. Pure functions/lookup tables only.
- `graph.py` is NOT modified. Integration happens by changing the body of `stub_planning_engine_node` in `aiconnex_agent/nodes/stub_nodes.py` to delegate to `real_planning_engine_node`, same pattern as the conversation parser wiring in Phase 3.
- Output contract must stay identical to the stub's return keys (`plan_steps`, `current_step_index`, `active_agent`) so `route_agent`/`route_after_evaluator` in `graph.py` keep working unchanged.
- Fallback resilience: unknown intents, invalid `target_agent` values, or an empty plan must never crash the node — always produce at least one safe, routable step.
- 100% test coverage per sub-module plus a node-level integration test covering all 5 known intents.

---

### Task 1: IntentPlanMapper Sub-module

**Files:**
- Create: `aiconnex_agent/planning/__init__.py`
- Create: `aiconnex_agent/planning/intent_plan_mapper.py`
- Test: `tests/test_planning_intent_mapper.py`

**Interfaces:**
- `IntentPlanMapper.get_plan(intent: str) -> List[Dict[str, Any]]` → returns an ordered list of raw step dicts (`step_id`, `target_agent`, `task`) for a given `primary_intent` string pulled from `cuc.goal["primary_intent"]`.

**Mapping table (deterministic business rule):**

| `primary_intent` | Plan steps (in order) |
|---|---|
| `compile_zip` | scout: "Discover archive structure & run UnifiedCompiler" → memory: "Persist compiled dataset session context" |
| `train_rul` | scout: "Compile/profile dataset if not already compiled" → platform: "Train RUL/regression model via ML pipeline" → memory: "Persist model run results" |
| `detect_anomalies` | scout: "Compile/profile dataset if not already compiled" → platform: "Train anomaly detection model via ML pipeline" → memory: "Persist model run results" |
| `query_status` | memory: "Retrieve last session run status/metrics" |
| `general` / unknown | scout: "General discovery — inspect available data sources" |

- [ ] **Step 1: Write the failing test**

```python
# tests/test_planning_intent_mapper.py
import pytest
from aiconnex_agent.planning.intent_plan_mapper import IntentPlanMapper

def test_compile_zip_plan():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("compile_zip")
    assert steps[0]["target_agent"] == "scout"
    assert steps[-1]["target_agent"] == "memory"

def test_train_rul_plan_includes_platform():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("train_rul")
    agents = [s["target_agent"] for s in steps]
    assert agents == ["scout", "platform", "memory"]

def test_detect_anomalies_plan_includes_platform():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("detect_anomalies")
    agents = [s["target_agent"] for s in steps]
    assert agents == ["scout", "platform", "memory"]

def test_query_status_plan_is_memory_only():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("query_status")
    assert len(steps) == 1
    assert steps[0]["target_agent"] == "memory"

def test_unknown_intent_falls_back_to_scout_discovery():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("general")
    assert len(steps) == 1
    assert steps[0]["target_agent"] == "scout"

    steps_unknown = mapper.get_plan("totally_made_up_intent")
    assert steps_unknown[0]["target_agent"] == "scout"

def test_step_ids_are_unique_and_sequential():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("train_rul")
    ids = [s["step_id"] for s in steps]
    assert ids == ["step_1", "step_2", "step_3"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_planning_intent_mapper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aiconnex_agent.planning'`

- [ ] **Step 3: Write minimal implementation**

```python
# aiconnex_agent/planning/__init__.py
"""aiconnex_agent/planning package - deterministic Intent -> ExecutionPlan routing."""
```

```python
# aiconnex_agent/planning/intent_plan_mapper.py
"""
aiconnex_agent/planning/intent_plan_mapper.py
==============================================
Sub-module 1: Deterministic Intent -> raw plan step dict lookup table.
Zero LLM calls, zero I/O. Pure business-rule mapping.
"""

from __future__ import annotations
from typing import Any, Dict, List


class IntentPlanMapper:
    """Maps a validated CUC primary_intent string to an ordered list of raw plan steps."""

    # Each entry is a list of (target_agent, task_description) tuples, in execution order.
    _PLAN_TEMPLATES: Dict[str, List[tuple]] = {
        "compile_zip": [
            ("scout", "Discover archive structure & run UnifiedCompiler"),
            ("memory", "Persist compiled dataset session context"),
        ],
        "train_rul": [
            ("scout", "Compile/profile dataset if not already compiled"),
            ("platform", "Train RUL/regression model via ML pipeline"),
            ("memory", "Persist model run results"),
        ],
        "detect_anomalies": [
            ("scout", "Compile/profile dataset if not already compiled"),
            ("platform", "Train anomaly detection model via ML pipeline"),
            ("memory", "Persist model run results"),
        ],
        "query_status": [
            ("memory", "Retrieve last session run status/metrics"),
        ],
    }

    _FALLBACK_TEMPLATE: List[tuple] = [
        ("scout", "General discovery — inspect available data sources"),
    ]

    def get_plan(self, intent: str) -> List[Dict[str, Any]]:
        """Return ordered raw step dicts for the given primary_intent. Never returns an empty list."""
        template = self._PLAN_TEMPLATES.get(intent, self._FALLBACK_TEMPLATE)
        return [
            {"step_id": f"step_{i + 1}", "target_agent": agent, "task": task}
            for i, (agent, task) in enumerate(template)
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_planning_intent_mapper.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add aiconnex_agent/planning/__init__.py aiconnex_agent/planning/intent_plan_mapper.py tests/test_planning_intent_mapper.py
git commit -m "feat(planning): implement deterministic IntentPlanMapper sub-module"
```

---

### Task 2: TaskStep/ExecutionPlan Contracts & PlanValidator Sub-module

**Files:**
- Modify: `aiconnex_agent/schemas.py` (add `TaskStep`, `ExecutionPlan` models)
- Create: `aiconnex_agent/planning/plan_validator.py`
- Test: `tests/test_planning_plan_validator.py`

**Interfaces:**
- `TaskStep(BaseModel)` → `step_id: str`, `target_agent: Literal["scout", "platform", "memory"]`, `task: str`
- `ExecutionPlan(BaseModel)` → `steps: List[TaskStep]`, `source_intent: str`
- `PlanValidator.validate(raw_steps: List[Dict], source_intent: str) -> ExecutionPlan` → drops any step with an invalid `target_agent`; if the resulting plan is empty, substitutes one safe fallback step so the graph always has somewhere to route.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_planning_plan_validator.py
import pytest
from aiconnex_agent.schemas import ExecutionPlan, TaskStep
from aiconnex_agent.planning.plan_validator import PlanValidator

def test_valid_plan_passes_through():
    validator = PlanValidator()
    raw = [
        {"step_id": "step_1", "target_agent": "scout", "task": "Discover archive"},
        {"step_id": "step_2", "target_agent": "platform", "task": "Train model"},
    ]
    plan = validator.validate(raw, source_intent="train_rul")
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 2
    assert plan.steps[0].target_agent == "scout"
    assert plan.source_intent == "train_rul"

def test_invalid_agent_step_is_dropped():
    validator = PlanValidator()
    raw = [
        {"step_id": "step_1", "target_agent": "scout", "task": "Discover archive"},
        {"step_id": "step_2", "target_agent": "not_a_real_agent", "task": "Do something invalid"},
    ]
    plan = validator.validate(raw, source_intent="compile_zip")
    assert len(plan.steps) == 1
    assert plan.steps[0].target_agent == "scout"

def test_all_invalid_steps_fall_back_to_safe_default():
    validator = PlanValidator()
    raw = [{"step_id": "step_1", "target_agent": "rogue_agent", "task": "bad"}]
    plan = validator.validate(raw, source_intent="general")
    assert len(plan.steps) == 1
    assert plan.steps[0].target_agent == "scout"

def test_empty_input_falls_back_to_safe_default():
    validator = PlanValidator()
    plan = validator.validate([], source_intent="general")
    assert len(plan.steps) == 1
    assert plan.steps[0].target_agent == "scout"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_planning_plan_validator.py -v`
Expected: FAIL with `ImportError: cannot import name 'ExecutionPlan' from 'aiconnex_agent.schemas'`

- [ ] **Step 3: Write minimal implementation**

Append to `aiconnex_agent/schemas.py`:

```python
# ---------------------------------------------------------------------------
# 6. Planning Engine Contracts
# ---------------------------------------------------------------------------

from typing import Literal


class TaskStep(BaseModel):
    """A single routed unit of work targeting one downstream agent."""
    step_id: str = Field(..., description="Sequential step identifier, e.g. step_1")
    target_agent: Literal["scout", "platform", "memory"] = Field(..., description="Agent responsible for this step")
    task: str = Field(..., description="Human-readable task description")


class ExecutionPlan(BaseModel):
    """Ordered set of TaskSteps produced by the Planning Engine for one CUC."""
    steps: List[TaskStep] = Field(default_factory=list)
    source_intent: str = Field(default="general", description="primary_intent that produced this plan")
```

```python
# aiconnex_agent/planning/plan_validator.py
"""
aiconnex_agent/planning/plan_validator.py
==========================================
Sub-module 2: Validates raw plan step dicts into a strongly-typed ExecutionPlan.
Guarantees the plan is never empty/unroutable.
"""

from __future__ import annotations
from typing import Any, Dict, List
from aiconnex_agent.schemas import ExecutionPlan, TaskStep

_VALID_AGENTS = {"scout", "platform", "memory"}

_SAFE_FALLBACK_STEP: Dict[str, Any] = {
    "step_id": "step_1",
    "target_agent": "scout",
    "task": "General discovery — inspect available data sources",
}


class PlanValidator:
    """Validates and sanitizes raw plan step dicts into an ExecutionPlan contract."""

    def validate(self, raw_steps: List[Dict[str, Any]], source_intent: str = "general") -> ExecutionPlan:
        """Drop invalid steps; guarantee at least one safe, routable step remains."""
        valid_steps: List[TaskStep] = []
        for raw in raw_steps:
            if raw.get("target_agent") not in _VALID_AGENTS:
                continue
            try:
                valid_steps.append(TaskStep(**raw))
            except Exception:
                continue

        if not valid_steps:
            valid_steps = [TaskStep(**_SAFE_FALLBACK_STEP)]

        return ExecutionPlan(steps=valid_steps, source_intent=source_intent)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_planning_plan_validator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add aiconnex_agent/schemas.py aiconnex_agent/planning/plan_validator.py tests/test_planning_plan_validator.py
git commit -m "feat(planning): add TaskStep/ExecutionPlan contracts and PlanValidator sub-module"
```

---

### Task 3: Planning Engine Orchestrator & LangGraph Node Integration

**Files:**
- Create: `aiconnex_agent/planning/planning_engine.py`
- Modify: `aiconnex_agent/nodes/stub_nodes.py` (redirect `stub_planning_engine_node` to delegate to `real_planning_engine_node`)
- Test: `tests/test_planning_engine_node.py`

**Interfaces:**
- `real_planning_engine_node(state: MasterAgentState) -> Dict[str, Any]` → reads `state.cuc.goal["primary_intent"]`, runs `IntentPlanMapper` → `PlanValidator`, returns `{"plan_steps": [...], "current_step_index": 0, "active_agent": <first step's target_agent>}` — identical output shape to the stub so `graph.py` requires no changes.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_planning_engine_node.py
import pytest
from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.schemas import ConversationUnderstandingContract
from aiconnex_agent.planning.planning_engine import real_planning_engine_node

@pytest.mark.parametrize("intent,expected_first_agent,expected_len", [
    ("compile_zip", "scout", 2),
    ("train_rul", "scout", 3),
    ("detect_anomalies", "scout", 3),
    ("query_status", "memory", 1),
    ("general", "scout", 1),
])
def test_planning_engine_routes_by_intent(intent, expected_first_agent, expected_len):
    state = MasterAgentState(cuc=ConversationUnderstandingContract(goal={"primary_intent": intent}))
    res = real_planning_engine_node(state)

    assert len(res["plan_steps"]) == expected_len
    assert res["plan_steps"][0]["target_agent"] == expected_first_agent
    assert res["current_step_index"] == 0
    assert res["active_agent"] == expected_first_agent

def test_planning_engine_handles_missing_intent_gracefully():
    state = MasterAgentState()  # no cuc.goal set at all
    res = real_planning_engine_node(state)
    assert len(res["plan_steps"]) >= 1
    assert res["active_agent"] in {"scout", "platform", "memory"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_planning_engine_node.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aiconnex_agent.planning.planning_engine'`

- [ ] **Step 3: Write minimal implementation**

```python
# aiconnex_agent/planning/planning_engine.py
"""
aiconnex_agent/planning/planning_engine.py
===========================================
Main Planning Engine Orchestrator running the 2 sub-modules:
  1. IntentPlanMapper
  2. PlanValidator
Replaces stub_planning_engine_node with real deterministic CUC -> ExecutionPlan routing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.planning.intent_plan_mapper import IntentPlanMapper
from aiconnex_agent.planning.plan_validator import PlanValidator

logger = logging.getLogger(__name__)

# Module singletons
intent_plan_mapper = IntentPlanMapper()
plan_validator = PlanValidator()


def real_planning_engine_node(state: MasterAgentState) -> Dict[str, Any]:
    """Real Planning Engine Node: CUC primary_intent -> validated ExecutionPlan."""
    logger.info("[PlanningEngine] Executing intent -> plan routing")
    intent = state.cuc.goal.get("primary_intent", "general")

    raw_steps = intent_plan_mapper.get_plan(intent)
    plan = plan_validator.validate(raw_steps, source_intent=intent)

    plan_steps = [step.model_dump() if hasattr(step, "model_dump") else step.dict() for step in plan.steps]
    first_agent = plan_steps[0]["target_agent"]

    return {
        "plan_steps": plan_steps,
        "current_step_index": 0,
        "active_agent": first_agent,
    }
```

Then modify `aiconnex_agent/nodes/stub_nodes.py` — replace the body of `stub_planning_engine_node` to delegate:

```python
def stub_planning_engine_node(state: MasterAgentState) -> Dict[str, Any]:
    """Delegates to the real IntentPlanMapper + PlanValidator Planning Engine Node."""
    from aiconnex_agent.planning.planning_engine import real_planning_engine_node
    return real_planning_engine_node(state)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_planning_engine_node.py -v`
Expected: PASS

Then run the full existing suite to confirm zero regressions (the graph topology tests exercise `stub_planning_engine_node` indirectly via `build_graph()`):

Run: `pytest tests/test_agent_state.py tests/test_stub_nodes.py tests/test_langgraph_topology.py tests/test_graph_runner.py tests/test_agent_contracts.py tests/test_parser_prompt_and_context.py tests/test_parser_extractor_and_validator.py tests/test_parser_scorer_and_generator.py tests/test_real_conversation_parser_node.py tests/test_tui_app.py tests/test_tui_dag_telemetry.py tests/test_tui_status_inspector.py tests/test_planning_intent_mapper.py tests/test_planning_plan_validator.py tests/test_planning_engine_node.py -v`
Expected: All PASS (note: `test_stub_nodes.py::test_stub_planning_engine_node` currently asserts the old hardcoded 3-step scout/platform/memory stub plan — this test must be updated in this step to assert against the new intent-driven output for whatever default `MasterAgentState()` produces, i.e. `general` intent → 1-step scout plan).

- [ ] **Step 5: Commit**

```bash
git add aiconnex_agent/planning/planning_engine.py aiconnex_agent/nodes/stub_nodes.py tests/test_planning_engine_node.py tests/test_stub_nodes.py
git commit -m "feat(planning): implement Planning Engine orchestrator and wire into LangGraph"
```

---

## Plan Self-Review

1. **Spec Coverage**:
   - Real Planning Engine replaces stub, consuming validated CUC from Phase 3.
   - Deterministic routing table covers all 5 intents the Conversation Parser can currently produce (`compile_zip`, `train_rul`, `detect_anomalies`, `query_status`, `general`).
   - `TaskStep`/`ExecutionPlan` Pydantic contracts added (closing the gap from the original Phase 0 vision that mentioned these models).
   - `graph.py` topology, `route_agent`, and `route_after_evaluator` require zero changes — output contract shape preserved exactly.
   - Fallback safety net guarantees the graph can never get stuck on an unroutable/empty plan.

2. **Placeholder Scan**: Zero TBD/TODO statements. All code is complete and runnable as written.

3. **Type Consistency**: `plan_steps` remains `List[Dict[str, Any]]` on `MasterAgentState` (unchanged field type) — `TaskStep`/`ExecutionPlan` are used internally for validation then dumped back to plain dicts, so no state schema migration is needed.

4. **Regression Awareness**: Explicitly calls out that `tests/test_stub_nodes.py::test_stub_planning_engine_node` (written in Phase 1 against the old hardcoded stub) needs updating in Task 3 since the delegation pattern changes its actual behavior — same precedent as Phase 3 Task 4 which updated the parser stub's behavior.

---

## Execution Choice

Plan complete and saved to `docs/superpowers/plans/2026-07-29-phase4-planning-engine.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
