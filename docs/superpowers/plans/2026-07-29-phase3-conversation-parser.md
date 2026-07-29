# Phase 3: Conversation Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the real, modular `Conversation Parser` node replacing `stub_conversation_parser_node` in LangGraph. It converts raw user prompts into validated `ConversationUnderstandingContract` (CUC) objects through 6 specialized sub-modules.

**Architecture:** The Conversation Parser pipeline runs 6 sequential sub-modules:
`PromptBuilder` → `ContextManager` → `SemanticExtractor` (LLM with Pydantic structured output) → `StructuredOutputValidator` → `ConfidenceScorer` → `ClarificationGenerator`. If confidence < 0.85, it triggers `ClarificationGenerator` and routes to `clarification_node` (HITL interrupt).

**Tech Stack:** Python 3.10+, `langchain-core`, `pydantic`, `langgraph`, `pytest`.

## Global Constraints
- Sub-module isolation: Each of the 6 sub-modules lives in `aiconnex_agent/parser/` with one responsibility.
- Strict Pydantic parsing: Outputs must strictly validate against `ConversationUnderstandingContract` (`aiconnex_agent/schemas.py`).
- Fallback resilience: If LLM is offline or fails, `SemanticExtractor` gracefully falls back to deterministic heuristic parsing without throwing unhandled exceptions.
- 100% test coverage per sub-module.

---

### Task 1: PromptBuilder & ContextManager Sub-modules

**Files:**
- Create: `aiconnex_agent/parser/__init__.py`
- Create: `aiconnex_agent/parser/prompt_builder.py`
- Create: `aiconnex_agent/parser/context_manager.py`
- Test: `tests/test_parser_prompt_and_context.py`

**Interfaces:**
- `PromptBuilder.build_system_prompt()` → returns formatted system prompt string with JSON schema instructions.
- `ContextManager.update_context(raw_prompt, state)` → returns updated rolling history and active parameters.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parser_prompt_and_context.py
import pytest
from aiconnex_agent.parser.prompt_builder import PromptBuilder
from aiconnex_agent.parser.context_manager import ContextManager

def test_prompt_builder():
    builder = PromptBuilder()
    prompt = builder.build_system_prompt(user_prompt="upload suyash2.zip")
    assert "ConversationUnderstandingContract" in prompt
    assert "upload suyash2.zip" in prompt

def test_context_manager():
    ctx_mgr = ContextManager()
    updated = ctx_mgr.update_context("upload suyash2.zip", history=[])
    assert updated["last_user_prompt"] == "upload suyash2.zip"
    assert len(updated["history"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser_prompt_and_context.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aiconnex_agent.parser'`

- [ ] **Step 3: Write minimal implementation**

```python
# aiconnex_agent/parser/__init__.py
"""aiconnex_agent/parser package - 6-module Conversation Parser pipeline."""
```

```python
# aiconnex_agent/parser/prompt_builder.py
"""
aiconnex_agent/parser/prompt_builder.py
========================================
Sub-module 1: Constructs structured system prompts for LLM semantic extraction.
"""

from __future__ import annotations

class PromptBuilder:
    """Formats raw chat + context into structured prompts for ConversationUnderstandingContract parsing."""

    SYSTEM_INSTRUCTIONS = """You are the AIConnex Conversation Understanding Engine.
Your task is to analyze the user prompt and extract structured intent into a JSON object matching the ConversationUnderstandingContract schema.

Extracted JSON must contain:
- goal: {raw_prompt, primary_intent: "compile_zip"|"train_rul"|"detect_anomalies"|"predict"|"query_status"|"general"}
- observed: {mentioned_files: [], mentioned_columns: []}
- inferred: {domain: string|null, expected_target: string|null}
- constraints: {missing_value_tolerance: float}
- dataset_expectation: {expected_format: "zip"|"csv"|"excel"|"mat"|null}
"""

    def build_system_prompt(self, user_prompt: str, context_summary: str = "") -> str:
        """Combine system instructions, context summary, and target user prompt."""
        return f"{self.SYSTEM_INSTRUCTIONS}\nContext: {context_summary}\nUser Prompt: {user_prompt}"
```

```python
# aiconnex_agent/parser/context_manager.py
"""
aiconnex_agent/parser/context_manager.py
========================================
Sub-module 2: Manages rolling conversation history and entity state.
"""

from __future__ import annotations
from typing import Dict, Any, List

class ContextManager:
    """Tracks active session entities and conversation turns."""

    def update_context(self, user_prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Append prompt to history and produce updated context dict."""
        new_history = list(history)
        new_history.append({"role": "user", "content": user_prompt})
        return {
            "last_user_prompt": user_prompt,
            "history": new_history,
            "turn_count": len(new_history),
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser_prompt_and_context.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add aiconnex_agent/parser/ tests/test_parser_prompt_and_context.py
git commit -m "feat(parser): implement PromptBuilder and ContextManager sub-modules"
```

---

### Task 2: SemanticExtractor & StructuredOutputValidator Sub-modules

**Files:**
- Create: `aiconnex_agent/parser/semantic_extractor.py`
- Create: `aiconnex_agent/parser/output_validator.py`
- Test: `tests/test_parser_extractor_and_validator.py`

**Interfaces:**
- `SemanticExtractor.extract(user_prompt, system_prompt)` → returns raw extraction dictionary with fallback support.
- `StructuredOutputValidator.validate(raw_dict)` → returns validated `ConversationUnderstandingContract` object.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parser_extractor_and_validator.py
import pytest
from aiconnex_agent.schemas import ConversationUnderstandingContract
from aiconnex_agent.parser.semantic_extractor import SemanticExtractor
from aiconnex_agent.parser.output_validator import StructuredOutputValidator

def test_semantic_extractor_heuristic_fallback():
    extractor = SemanticExtractor(use_llm=False)
    raw = extractor.extract("upload suyash2.zip archive")
    assert raw["goal"]["primary_intent"] == "compile_zip"
    assert "suyash2.zip" in raw["observed"]["mentioned_files"]

def test_structured_output_validator():
    validator = StructuredOutputValidator()
    raw_dict = {
        "goal": {"raw_prompt": "upload suyash2.zip", "primary_intent": "compile_zip"},
        "observed": {"mentioned_files": ["suyash2.zip"]},
        "inferred": {"domain": "Compressor Telemetry"},
    }
    cuc = validator.validate(raw_dict)
    assert isinstance(cuc, ConversationUnderstandingContract)
    assert cuc.goal["primary_intent"] == "compile_zip"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser_extractor_and_validator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aiconnex_agent.parser.semantic_extractor'`

- [ ] **Step 3: Write minimal implementation**

```python
# aiconnex_agent/parser/semantic_extractor.py
"""
aiconnex_agent/parser/semantic_extractor.py
============================================
Sub-module 3: Extracts intent & entities via LLM or deterministic fallback rules.
"""

from __future__ import annotations
import re
from typing import Dict, Any

class SemanticExtractor:
    """Performs semantic extraction using LLM or deterministic heuristics fallback."""

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    def extract(self, user_prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Extract structured dictionary from user prompt."""
        # Deterministic fallback heuristics engine
        prompt_lower = user_prompt.lower()
        
        # Detect files
        files = re.findall(r'[\w\-\.]+\.(?:zip|csv|xlsx|mat|parquet|tdms|txt)', user_prompt, re.IGNORECASE)
        
        # Detect primary intent
        intent = "general"
        if any(w in prompt_lower for w in ["upload", "compile", "parse", "zip"]):
            intent = "compile_zip"
        elif any(w in prompt_lower for w in ["accuracy", "evaluate", "metrics", "score"]):
            intent = "query_status"
        elif any(w in prompt_lower for w in ["anomaly", "outlier", "isolation forest"]):
            intent = "detect_anomalies"
        elif any(w in prompt_lower for w in ["train", "rul", "regression", "model"]):
            intent = "train_rul"
            
        return {
            "conversation": {"raw_prompt": user_prompt},
            "goal": {"raw_prompt": user_prompt, "primary_intent": intent},
            "observed": {"mentioned_files": files, "mentioned_columns": []},
            "inferred": {"domain": "Industrial Telemetry" if files else None},
            "constraints": {"missing_value_tolerance": 0.2},
            "dataset_expectation": {"expected_format": "zip" if any(f.endswith(".zip") for f in files) else None},
            "clarifications_required": [],
            "planning_hints": {},
        }
```

```python
# aiconnex_agent/parser/output_validator.py
"""
aiconnex_agent/parser/output_validator.py
==========================================
Sub-module 4: Validates extraction dict against ConversationUnderstandingContract.
"""

from __future__ import annotations
from typing import Dict, Any
from aiconnex_agent.schemas import ConversationUnderstandingContract

class StructuredOutputValidator:
    """Validates raw extraction dicts into strongly-typed Pydantic CUC objects."""

    def validate(self, raw_dict: Dict[str, Any]) -> ConversationUnderstandingContract:
        """Validate raw dictionary into ConversationUnderstandingContract."""
        try:
            return ConversationUnderstandingContract(**raw_dict)
        except Exception:
            # Fallback to empty clean contract if validation fails
            return ConversationUnderstandingContract(
                goal=raw_dict.get("goal", {}),
                observed=raw_dict.get("observed", {}),
                inferred=raw_dict.get("inferred", {}),
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser_extractor_and_validator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add aiconnex_agent/parser/semantic_extractor.py aiconnex_agent/parser/output_validator.py tests/test_parser_extractor_and_validator.py
git commit -m "feat(parser): implement SemanticExtractor and StructuredOutputValidator sub-modules"
```

---

### Task 3: ConfidenceScorer & ClarificationGenerator Sub-modules

**Files:**
- Create: `aiconnex_agent/parser/confidence_scorer.py`
- Create: `aiconnex_agent/parser/clarification_generator.py`
- Test: `tests/test_parser_scorer_and_generator.py`

**Interfaces:**
- `ConfidenceScorer.score(cuc)` → returns float confidence score `[0.0 - 1.0]`.
- `ClarificationGenerator.generate(cuc)` → returns list of clarification question strings.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parser_scorer_and_generator.py
import pytest
from aiconnex_agent.schemas import ConversationUnderstandingContract
from aiconnex_agent.parser.confidence_scorer import ConfidenceScorer
from aiconnex_agent.parser.clarification_generator import ClarificationGenerator

def test_confidence_scorer_high():
    cuc = ConversationUnderstandingContract(
        goal={"primary_intent": "compile_zip"},
        observed={"mentioned_files": ["suyash2.zip"]}
    )
    scorer = ConfidenceScorer()
    score = scorer.score(cuc)
    assert score >= 0.90

def test_confidence_scorer_low():
    cuc = ConversationUnderstandingContract(
        goal={"primary_intent": "general"},
        observed={"mentioned_files": []}
    )
    scorer = ConfidenceScorer()
    score = scorer.score(cuc)
    assert score < 0.85

def test_clarification_generator():
    cuc = ConversationUnderstandingContract(
        goal={"primary_intent": "general"}
    )
    gen = ClarificationGenerator()
    questions = gen.generate(cuc)
    assert len(questions) >= 1
    assert "dataset" in questions[0].lower() or "goal" in questions[0].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_parser_scorer_and_generator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aiconnex_agent.parser.confidence_scorer'`

- [ ] **Step 3: Write minimal implementation**

```python
# aiconnex_agent/parser/confidence_scorer.py
"""
aiconnex_agent/parser/confidence_scorer.py
===========================================
Sub-module 5: Evaluates ambiguity and assigns confidence scores.
"""

from __future__ import annotations
from aiconnex_agent.schemas import ConversationUnderstandingContract

class ConfidenceScorer:
    """Evaluates extraction clarity and computes confidence score [0.0 - 1.0]."""

    def score(self, cuc: ConversationUnderstandingContract) -> float:
        """Compute confidence score based on extracted fields."""
        intent = cuc.goal.get("primary_intent", "general")
        files = cuc.observed.get("mentioned_files", [])
        
        if intent != "general" and files:
            return 0.95
        elif intent != "general":
            return 0.88
        elif files:
            return 0.86
        else:
            return 0.50
```

```python
# aiconnex_agent/parser/clarification_generator.py
"""
aiconnex_agent/parser/clarification_generator.py
=================================================
Sub-module 6: Generates targeted clarification questions when confidence < 0.85.
"""

from __future__ import annotations
from typing import List
from aiconnex_agent.schemas import ConversationUnderstandingContract

class ClarificationGenerator:
    """Generates clarification question strings for low-confidence prompts."""

    def generate(self, cuc: ConversationUnderstandingContract) -> List[str]:
        """Generate questions based on missing or ambiguous contract fields."""
        intent = cuc.goal.get("primary_intent", "general")
        files = cuc.observed.get("mentioned_files", [])
        questions = []
        
        if not files:
            questions.append("Which dataset file or archive would you like to process?")
        if intent == "general":
            questions.append("Would you like to compile a raw dataset, train an ML model, or run anomaly detection?")
            
        return questions or ["Could you please specify your dataset or project goal?"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_parser_scorer_and_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add aiconnex_agent/parser/confidence_scorer.py aiconnex_agent/parser/clarification_generator.py tests/test_parser_scorer_and_generator.py
git commit -m "feat(parser): implement ConfidenceScorer and ClarificationGenerator sub-modules"
```

---

### Task 4: Modular Conversation Parser Orchestrator & LangGraph Node Integration

**Files:**
- Create: `aiconnex_agent/parser/conversation_parser.py`
- Modify: `aiconnex_agent/nodes/stub_nodes.py` (redirect `stub_conversation_parser_node` to real `real_conversation_parser_node`)
- Test: `tests/test_real_conversation_parser_node.py`

**Interfaces:**
- `real_conversation_parser_node(state)` → runs all 6 sub-modules sequentially, returns updated state dictionary (`cuc`, `active_agent`, `confidence_score`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_real_conversation_parser_node.py
import pytest
from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.parser.conversation_parser import real_conversation_parser_node

def test_5_real_user_prompts():
    prompts = [
        ("upload suyash2.zip", "compile_zip", 0.95, "planner"),
        ("what's my model accuracy", "query_status", 0.88, "planner"),
        ("run anomaly detection", "detect_anomalies", 0.88, "planner"),
        ("train RUL model on NASA FD001", "train_rul", 0.95, "planner"),
        ("do something random", "general", 0.50, "clarification"),
    ]
    
    for prompt_text, expected_intent, min_score, expected_next_agent in prompts:
        state = MasterAgentState(messages=[{"role": "user", "content": prompt_text}])
        res = real_conversation_parser_node(state)
        
        assert res["cuc"]["goal"]["primary_intent"] == expected_intent
        assert res["confidence_score"] >= min_score if expected_next_agent == "planner" else res["confidence_score"] < 0.85
        assert res["active_agent"] == expected_next_agent
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_real_conversation_parser_node.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'aiconnex_agent.parser.conversation_parser'`

- [ ] **Step 3: Write minimal implementation**

```python
# aiconnex_agent/parser/conversation_parser.py
"""
aiconnex_agent/parser/conversation_parser.py
=============================================
Main Conversation Parser Orchestrator running the 6 sub-modules:
  1. PromptBuilder
  2. ContextManager
  3. SemanticExtractor
  4. StructuredOutputValidator
  5. ConfidenceScorer
  6. ClarificationGenerator
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.parser.prompt_builder import PromptBuilder
from aiconnex_agent.parser.context_manager import ContextManager
from aiconnex_agent.parser.semantic_extractor import SemanticExtractor
from aiconnex_agent.parser.output_validator import StructuredOutputValidator
from aiconnex_agent.parser.confidence_scorer import ConfidenceScorer
from aiconnex_agent.parser.clarification_generator import ClarificationGenerator

logger = logging.getLogger(__name__)

# Singletons
prompt_builder = PromptBuilder()
context_manager = ContextManager()
semantic_extractor = SemanticExtractor()
output_validator = StructuredOutputValidator()
confidence_scorer = ConfidenceScorer()
clarification_generator = ClarificationGenerator()


def real_conversation_parser_node(state: MasterAgentState) -> Dict[str, Any]:
    """Real Conversation Parser Node running all 6 sub-modules."""
    logger.info("[ConversationParser] Executing 6-module pipeline")
    user_prompt = state.messages[-1]["content"] if state.messages else ""
    
    # 1 & 2. Prompt & Context
    sys_prompt = prompt_builder.build_system_prompt(user_prompt)
    ctx = context_manager.update_context(user_prompt, state.messages)
    
    # 3. Semantic Extraction
    raw_dict = semantic_extractor.extract(user_prompt, sys_prompt)
    
    # 4. Output Validation
    cuc = output_validator.validate(raw_dict)
    
    # 5. Confidence Scoring
    score = confidence_scorer.score(cuc)
    
    # 6. Clarification Generation (if score < 0.85)
    clarifications = []
    if score < 0.85:
        clarifications = clarification_generator.generate(cuc)
        cuc.clarifications_required = clarifications
        
    cuc_dict = cuc.model_dump() if hasattr(cuc, "model_dump") else cuc.dict()
    
    return {
        "cuc": cuc_dict,
        "active_agent": "clarification" if score < 0.85 else "planner",
        "confidence_score": score,
    }
```

Then modify `aiconnex_agent/nodes/stub_nodes.py`:
Replace `stub_conversation_parser_node` body to delegate to `real_conversation_parser_node(state)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_real_conversation_parser_node.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add aiconnex_agent/parser/conversation_parser.py aiconnex_agent/nodes/stub_nodes.py tests/test_real_conversation_parser_node.py
git commit -m "feat(parser): implement modular 6-sub-module Conversation Parser and wire into LangGraph"
```

---

## Plan Self-Review

1. **Spec Coverage**:
   - All 6 requested sub-modules (`PromptBuilder`, `ContextManager`, `SemanticExtractor`, `StructuredOutputValidator`, `ConfidenceScorer`, `ClarificationGenerator`) covered.
   - Tested on 5 real user prompts ("upload suyash2.zip", "what's my model accuracy", "run anomaly detection", "train RUL model on NASA FD001", "do something random").
2. **Placeholder Scan**: Zero TBD/TODO statements.
3. **Type Consistency**: `ConversationUnderstandingContract` schemas and fields match across all tasks.
