"""
Pydantic models for the pre-upload conversation contract.

Mirrors the JSON contract schema shown in the spec, with every field
type-annotated so merge/validation logic is checked, not just raw dict
manipulation.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Nested models (each maps to a JSON object key)
# ──────────────────────────────────────────────


class CandidateMLProblemType(BaseModel):
    type: str = ""
    confidence: float = 0.0


class Goal(BaseModel):
    primary_goal: str = ""
    secondary_goals: list[str] = Field(default_factory=list)
    business_problem: str = ""
    candidate_ml_problem_types: list[CandidateMLProblemType] = Field(default_factory=list)


class Observed(BaseModel):
    industry_terms: list[str] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    datasets_mentioned: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    time_periods: list[str] = Field(default_factory=list)
    quantities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    user_statements: list[str] = Field(default_factory=list)


class InferredField(BaseModel):
    value: str = ""
    confidence: float = 0.0


class Inferred(BaseModel):
    industry: InferredField = Field(default_factory=InferredField)
    user_role: InferredField = Field(default_factory=InferredField)
    business_domain: InferredField = Field(default_factory=InferredField)
    experience_level: InferredField = Field(default_factory=InferredField)


class DatasetExpectation(BaseModel):
    upload_status: str = "pending"
    expected_file_types: list[str] = Field(default_factory=list)
    expected_dataset_type: str = ""
    expected_duration: str = ""
    expected_sampling_rate: str = ""
    expected_size: str = ""


class Constraints(BaseModel):
    preferred_algorithms: list[str] = Field(default_factory=list)
    preferred_frameworks: list[str] = Field(default_factory=list)
    explainability_required: Optional[bool] = None  # None = not yet asked, True/False = answered
    deployment_constraints: list[str] = Field(default_factory=list)
    business_constraints: list[str] = Field(default_factory=list)
    technical_constraints: list[str] = Field(default_factory=list)


class Urgency(BaseModel):
    value: str = ""
    confidence: float = 0.0


class ConversationAnalysis(BaseModel):
    urgency: Urgency = Field(default_factory=Urgency)
    sentiment: str = ""
    certainty_level: str = ""
    ambiguity_detected: bool = False
    missing_information: list[str] = Field(default_factory=list)


class ClarificationItem(BaseModel):
    question: str = ""
    reason: str = ""
    priority: str = "high"


class PlanningHints(BaseModel):
    recommended_next_action: str = ""
    recommended_agents: list[str] = Field(default_factory=list)
    wait_for_dataset: bool = True
    conversation_complete: bool = False


class Metadata(BaseModel):
    llm_model: str = ""
    parser_version: str = ""
    processing_time_ms: int = 0


# ──────────────────────────────────────────────
# Top-level contract
# ──────────────────────────────────────────────


class PreUploadContract(BaseModel):
    """The full pre-upload conversation contract, written to disk after every turn."""

    schema_version: str = "1.0"

    conversation: ConversationMeta = Field(default_factory=lambda: ConversationMeta())
    goal: Goal = Field(default_factory=Goal)
    observed: Observed = Field(default_factory=Observed)
    inferred: Inferred = Field(default_factory=Inferred)
    dataset_expectation: DatasetExpectation = Field(default_factory=DatasetExpectation)
    constraints: Constraints = Field(default_factory=Constraints)
    conversation_analysis: ConversationAnalysis = Field(default_factory=ConversationAnalysis)
    clarifications_required: list[ClarificationItem] = Field(default_factory=list)
    planning_hints: PlanningHints = Field(default_factory=PlanningHints)
    metadata: Metadata = Field(default_factory=Metadata)


class ConversationMeta(BaseModel):
    session_id: str = ""
    conversation_id: str = ""
    timestamp: str = ""
    phase: str = "pre_upload"
    dataset_uploaded: bool = False
    conversation_turn: int = 1


# ──────────────────────────────────────────────
# Turn-level extraction output (not the full contract)
# ──────────────────────────────────────────────


class TurnExtraction(BaseModel):
    """What the LLM returns for a single turn — only the fields it found
    new or updated information for, each with its own confidence score."""

    # Goal
    primary_goal: Optional[str] = None
    primary_goal_confidence: float = 0.0
    secondary_goals: Optional[list[str]] = None
    secondary_goals_confidence: float = 0.0
    business_problem: Optional[str] = None
    business_problem_confidence: float = 0.0
    candidate_ml_problem_types: Optional[list[CandidateMLProblemType]] = None
    candidate_ml_problem_types_confidence: float = 0.0

    # Observed
    industry_terms: Optional[list[str]] = None
    equipment: Optional[list[str]] = None
    assets: Optional[list[str]] = None
    datasets_mentioned: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    time_periods: Optional[list[str]] = None
    quantities: Optional[list[str]] = None
    keywords: Optional[list[str]] = None
    user_statements: Optional[list[str]] = None

    # Inferred
    industry: Optional[str] = None
    industry_confidence: float = 0.0
    user_role: Optional[str] = None
    user_role_confidence: float = 0.0
    business_domain: Optional[str] = None
    business_domain_confidence: float = 0.0
    experience_level: Optional[str] = None
    experience_level_confidence: float = 0.0

    # Dataset expectation
    expected_file_types: Optional[list[str]] = None
    expected_file_types_confidence: float = 0.0
    expected_dataset_type: Optional[str] = None
    expected_dataset_type_confidence: float = 0.0
    expected_duration: Optional[str] = None
    expected_duration_confidence: float = 0.0
    expected_sampling_rate: Optional[str] = None
    expected_sampling_rate_confidence: float = 0.0
    expected_size: Optional[str] = None
    expected_size_confidence: float = 0.0

    # Constraints
    preferred_algorithms: Optional[list[str]] = None
    preferred_frameworks: Optional[list[str]] = None
    explainability_required: Optional[bool] = None
    explainability_required_confidence: float = 0.0
    deployment_constraints: Optional[list[str]] = None
    business_constraints: Optional[list[str]] = None
    technical_constraints: Optional[list[str]] = None

    # Conversation analysis
    urgency: Optional[str] = None
    urgency_confidence: float = 0.0
    sentiment: Optional[str] = None
    certainty_level: Optional[str] = None
    ambiguity_detected: Optional[bool] = None

    # Planning
    recommended_next_action: Optional[str] = None
    wait_for_dataset: Optional[bool] = None