"""
Schema definitions for the structured output the extraction layer produces,
and for the validated result after grounding against real pipeline state.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from intents import VALID_INTENTS


class ExtractedEntities(BaseModel):
    """Entities the LLM may pull out of a prompt. All optional here —
    per-intent *requiredness* is checked separately in validation.py,
    since which fields matter depends on the intent."""

    dataset_id: Optional[str] = None
    dag_id: Optional[str] = None
    recipe_name: Optional[str] = None
    target_environment: Optional[str] = None


class ExtractedIntent(BaseModel):
    """Raw output of the extraction step, before grounding/validation."""

    intent: str
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None  # short model-provided justification, optional

    @field_validator("intent")
    @classmethod
    def intent_must_be_known(cls, v: str) -> str:
        if v not in VALID_INTENTS:
            # Don't hard-fail here -- let the dispatcher route unknown
            # intents to out_of_scope/clarification handling instead of
            # crashing the request.
            return "out_of_scope"
        return v


class ValidationOutcome(BaseModel):
    """Result of checking an ExtractedIntent against real pipeline state."""

    ok: bool
    missing_entities: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    needs_confirmation: bool = False
