"""
aiconnex_agent/registries/registry_loader.py
==============================================
Loads and validates the three Pre-Upload v1 registries:
  - required_fields.yaml
  - conversation_rules.yaml
  - upload_readiness_rules.yaml

Fails fast at load time on malformed YAML/missing required keys, so a bad
registry edit surfaces immediately rather than silently misbehaving deep
inside conversation_planner_node at runtime.

Also provides evaluate_field_rule(), a small dotted-path field getter +
rule evaluator so conversation_planner_node/contract_manager_node don't
need to duplicate "how do I read goal.task_family off a CUC" logic.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

_REGISTRY_DIR = Path(__file__).resolve().parent

_VALID_RULES = {"not_default", "non_empty", "min_value"}


# ---------------------------------------------------------------------------
# Typed registry models (validated at load time)
# ---------------------------------------------------------------------------

class RequiredFieldRule(BaseModel):
    field: str
    rule: str
    description: str = ""
    default_value: Optional[Any] = None
    threshold: Optional[float] = None

    @field_validator("rule")
    @classmethod
    def _rule_must_be_known(cls, v: str) -> str:
        if v not in _VALID_RULES:
            raise ValueError(f"Unknown rule '{v}'. Valid rules: {sorted(_VALID_RULES)}")
        return v

    @field_validator("field")
    @classmethod
    def _field_must_be_dotted_path(cls, v: str) -> str:
        if not v or "." not in v:
            raise ValueError(f"'field' must be a dotted path (e.g. 'goal.task_family'), got: {v!r}")
        return v


class OptionalFieldEntry(BaseModel):
    field: str
    description: str = ""


class RequiredFieldsRegistry(BaseModel):
    required: List[RequiredFieldRule] = Field(default_factory=list)
    optional: List[OptionalFieldEntry] = Field(default_factory=list)


class ConversationRules(BaseModel):
    max_questions_per_turn: int = 1
    avoid_repeat_questions: bool = True
    always_summarize_before_upload: bool = True
    stall_warning_after_turns: int = 6
    surface_contradictions: bool = True

    @field_validator("max_questions_per_turn", "stall_warning_after_turns")
    @classmethod
    def _must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Turn/question counters must be >= 1")
        return v


class UploadReadinessRules(BaseModel):
    all_required_fields_satisfied: bool = True
    no_unresolved_contradictions: bool = True


# ---------------------------------------------------------------------------
# YAML loading (cached — files are read once per process)
# ---------------------------------------------------------------------------

def _load_yaml(filename: str) -> Dict[str, Any]:
    path = _REGISTRY_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Registry file {filename} did not parse to a mapping (got {type(data).__name__})")
    return data


@functools.lru_cache(maxsize=1)
def get_required_fields() -> RequiredFieldsRegistry:
    raw = _load_yaml("required_fields.yaml")
    pre_upload = raw.get("pre_upload")
    if not isinstance(pre_upload, dict):
        raise ValueError("required_fields.yaml must contain a top-level 'pre_upload' mapping")
    return RequiredFieldsRegistry.model_validate(pre_upload)


@functools.lru_cache(maxsize=1)
def get_conversation_rules() -> ConversationRules:
    raw = _load_yaml("conversation_rules.yaml")
    rules = raw.get("rules")
    if not isinstance(rules, dict):
        raise ValueError("conversation_rules.yaml must contain a top-level 'rules' mapping")
    return ConversationRules.model_validate(rules)


@functools.lru_cache(maxsize=1)
def get_upload_readiness_rules() -> UploadReadinessRules:
    raw = _load_yaml("upload_readiness_rules.yaml")
    ready_if = raw.get("ready_if")
    if not isinstance(ready_if, dict):
        raise ValueError("upload_readiness_rules.yaml must contain a top-level 'ready_if' mapping")
    return UploadReadinessRules.model_validate(ready_if)


def clear_registry_cache() -> None:
    """Test/hot-reload helper: forces registries to be re-read from disk on next access."""
    get_required_fields.cache_clear()
    get_conversation_rules.cache_clear()
    get_upload_readiness_rules.cache_clear()


# ---------------------------------------------------------------------------
# Dotted-path field access + rule evaluation
# ---------------------------------------------------------------------------

def get_field_value(obj: Any, dotted_path: str) -> Any:
    """Resolve a dotted path (e.g. 'goal.task_family') against a Pydantic
    model or dict, returning None if any segment is missing."""
    current = obj
    for part in dotted_path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def evaluate_field_rule(obj: Any, rule: RequiredFieldRule) -> bool:
    """Return True if `obj`'s field at rule.field satisfies rule.rule."""
    value = get_field_value(obj, rule.field)

    if rule.rule == "not_default":
        return value is not None and value != "" and value != rule.default_value
    if rule.rule == "non_empty":
        if value is None:
            return False
        if isinstance(value, (str, list, dict)):
            return len(value) > 0
        return True
    if rule.rule == "min_value":
        try:
            return value is not None and float(value) >= float(rule.threshold)
        except (TypeError, ValueError):
            return False
    # Unreachable: RequiredFieldRule validator already restricts to known rules.
    raise ValueError(f"Unhandled rule type: {rule.rule}")


def get_missing_required_fields(obj: Any) -> List[RequiredFieldRule]:
    """Return the list of required-field rules from the registry that `obj`
    does not currently satisfy."""
    registry = get_required_fields()
    return [rule for rule in registry.required if not evaluate_field_rule(obj, rule)]
