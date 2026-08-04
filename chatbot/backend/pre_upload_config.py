"""
Field-tier configuration for the pre-upload intent-gathering flow.

Defines which contract fields are REQUIRED, RECOMMENDED, or OPPORTUNISTIC,
along with confidence thresholds used throughout the merge/gap-analysis logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ──────────────────────────────────────────────
# Confidence thresholds
# ──────────────────────────────────────────────

# Minimum confidence to accept a new value during merge (below this = noise)
MIN_CONFIDENCE_TO_ACCEPT: float = 0.4

# REQUIRED fields must reach this confidence to be considered "filled"
REQUIRED_CONFIDENCE_THRESHOLD: float = 0.7

# RECOMMENDED fields are considered "filled" at this lower bar
RECOMMENDED_CONFIDENCE_THRESHOLD: float = 0.5

# Number of consecutive ambiguous turns before offering quick-select
MAX_AMBIGUOUS_TURNS: int = 2

# Number of times the same field can be asked about before offering quick-select
MAX_ASKED_SAME_FIELD: int = 2


# ──────────────────────────────────────────────
# Field tier definitions
# ──────────────────────────────────────────────

# Each entry is a dot-separated path into the PreUploadContract,
# e.g. "goal.primary_goal" means contract.goal.primary_goal.
# The "confidence_field" tells us which TurnExtraction field holds
# the confidence for this value.

@dataclass
class FieldTierEntry:
    path: str                     # dot-path in PreUploadContract, e.g. "goal.primary_goal"
    confidence_field: str         # field name in TurnExtraction, e.g. "primary_goal_confidence"
    label: str = ""               # human-readable label for questions


REQUIRED_FIELDS: list[FieldTierEntry] = [
    FieldTierEntry("goal.primary_goal", "primary_goal_confidence", "your primary goal"),
    FieldTierEntry("goal.candidate_ml_problem_types", "candidate_ml_problem_types_confidence", "the type of ML problem"),
    FieldTierEntry("dataset_expectation.expected_dataset_type", "expected_dataset_type_confidence", "the type of dataset"),
    FieldTierEntry("dataset_expectation.expected_file_types", "expected_file_types_confidence", "the file format(s)"),
]

RECOMMENDED_FIELDS: list[FieldTierEntry] = [
    FieldTierEntry("inferred.industry", "industry_confidence", "your industry"),
    FieldTierEntry("inferred.user_role", "user_role_confidence", "your role"),
    FieldTierEntry("constraints.explainability_required", "explainability_required_confidence", "explainability requirements"),
]

OPPORTUNISTIC_FIELDS: list[FieldTierEntry] = [
    FieldTierEntry("goal.secondary_goals", "secondary_goals_confidence"),
    FieldTierEntry("observed.locations", "",),
    FieldTierEntry("observed.time_periods", "",),
    FieldTierEntry("observed.quantities", "",),
]


def get_all_tiered_fields() -> list[FieldTierEntry]:
    """Return all fields across all tiers (for building prompts)."""
    return REQUIRED_FIELDS + RECOMMENDED_FIELDS + OPPORTUNISTIC_FIELDS