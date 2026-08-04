"""
Validation layer: takes an ExtractedIntent and checks it against
(1) the required-entities spec for that intent, and
(2) real pipeline state (does the dataset exist, has the right prior
    stage completed).

This is the "deterministic gate" between the probabilistic LLM extraction
and anything that actually executes -- see the architecture doc's hybrid
pattern.
"""

from intents import required_entities, RiskTier, get_risk_tier
from schemas import ExtractedIntent, ValidationOutcome
import pipeline_state as ps

# Which prior stage must be complete before this intent's action can run.
# None means no prior-stage dependency.
PREREQUISITES = {
    "run_dag_verification": ("profiled", "Dataset must be profiled before running DAG verification."),
    "compile_training_recipe": ("dag_verified", "DAG must be verified before compiling a training recipe."),
    "deploy_pipeline": ("recipe_compiled", "A training recipe must be compiled before deployment."),
}


def validate(extracted: ExtractedIntent) -> ValidationOutcome:
    errors: list[str] = []
    missing: list[str] = []

    # 1. Required-entity check (schema-level, no state lookup needed)
    entities_dict = extracted.entities.model_dump()
    for field in required_entities(extracted.intent):
        if not entities_dict.get(field):
            missing.append(field)

    if missing:
        return ValidationOutcome(ok=False, missing_entities=missing, errors=errors)

    # 2. Grounding against real state (only if a dataset_id was required/provided)
    dataset_id = entities_dict.get("dataset_id")
    if dataset_id and extracted.intent not in ("run_dataset_profiling",):
        if not ps.dataset_exists(dataset_id):
            errors.append(f"Dataset '{dataset_id}' was not found in the registry.")
            return ValidationOutcome(ok=False, missing_entities=missing, errors=errors)

    # run_dataset_profiling can reference a brand-new dataset_id -- register it
    if dataset_id and extracted.intent == "run_dataset_profiling" and not ps.dataset_exists(dataset_id):
        ps.register_dataset(dataset_id)

    # 3. Prerequisite stage check
    if dataset_id and extracted.intent in PREREQUISITES:
        required_flag, message = PREREQUISITES[extracted.intent]
        state = ps.get_dataset_state(dataset_id) or {}
        if not state.get(required_flag):
            errors.append(message)
            return ValidationOutcome(ok=False, missing_entities=missing, errors=errors)

    # 4. Risk-tier confirmation requirement
    risk = get_risk_tier(extracted.intent)
    needs_confirmation = risk == RiskTier.HIGH_IMPACT

    return ValidationOutcome(ok=True, missing_entities=[], errors=[], needs_confirmation=needs_confirmation)
