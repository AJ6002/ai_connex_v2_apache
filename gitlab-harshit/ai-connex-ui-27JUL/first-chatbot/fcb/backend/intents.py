"""
Intent taxonomy for the AI Connexx chatbot.

This is the single source of truth for what the chatbot understands.
Every intent has:
  - a canonical name (used everywhere else in the backend)
  - a risk tier: "read_only", "low_impact", or "high_impact"
      read_only    -> answer directly, no confirmation needed
      low_impact   -> proceed, but log clearly (e.g. kicking off a profiling job)
      high_impact  -> require explicit user confirmation before dispatching
  - a short description (used to build the extraction prompt)
  - example phrasings (used to build the extraction prompt, and later as a
    labeled example bank if an embedding-similarity check is added)
  - expected entity fields (used for schema validation)
"""

from enum import Enum


class RiskTier(str, Enum):
    READ_ONLY = "read_only"
    LOW_IMPACT = "low_impact"
    HIGH_IMPACT = "high_impact"


# Each intent's entity spec: field_name -> whether it's required
INTENT_TAXONOMY = {
    "get_dataset_status": {
        "risk_tier": RiskTier.READ_ONLY,
        "description": "Check the profiling / validation status or score of a dataset that has already been uploaded.",
        "examples": [
            "What's the validation score for the sales dataset?",
            "Check the status of my last dataset upload",
            "Did the sensor_data.csv dataset pass validation?",
            "Show me the profiling results for dataset123",
        ],
        "entities": {"dataset_id": True},
    },
    "run_dataset_profiling": {
        "risk_tier": RiskTier.LOW_IMPACT,
        "description": "Trigger the Dataset Profiler (meta1) stage on an uploaded dataset to analyze columns and recommend a DAG/algorithm family.",
        "examples": [
            "Profile the new sensor_data.csv dataset",
            "Run the dataset profiler on sales_q3",
            "Analyze the dataset I just uploaded",
        ],
        "entities": {"dataset_id": True},
    },
    "get_dag_status": {
        "risk_tier": RiskTier.READ_ONLY,
        "description": "Check the DAG Execution (meta2) status or which DAG schema was matched for a dataset.",
        "examples": [
            "What DAG was matched for the sales dataset?",
            "Check DAG execution status for dataset123",
            "Is the DAG verification done yet?",
        ],
        "entities": {"dataset_id": True, "dag_id": False},
    },
    "run_dag_verification": {
        "risk_tier": RiskTier.LOW_IMPACT,
        "description": "Trigger the DAG Execution (meta2) stage: run/verify the matched DAG schema for a profiled dataset.",
        "examples": [
            "Run DAG verification on the sales dataset",
            "Verify the DAG schema for dataset123",
            "Kick off DAG execution now",
        ],
        "entities": {"dataset_id": True, "dag_id": False},
    },
    "get_recipe_status": {
        "risk_tier": RiskTier.READ_ONLY,
        "description": "Check the Recipe Orchestrator (meta3) status or compiled training recipe for a dataset/DAG.",
        "examples": [
            "What's the compiled recipe for the sales dataset?",
            "Check recipe orchestrator status",
            "Has the training recipe been compiled yet?",
        ],
        "entities": {"dataset_id": True, "dag_id": False},
    },
    "compile_training_recipe": {
        "risk_tier": RiskTier.LOW_IMPACT,
        "description": "Trigger the Recipe Orchestrator (meta3) stage: merge boilerplate configs into an executable training recipe blueprint.",
        "examples": [
            "Compile the training recipe for the sales dataset",
            "Generate the recipe blueprint now",
            "Merge the configs into a training recipe",
        ],
        "entities": {"dataset_id": True, "dag_id": False, "recipe_name": False},
    },
    "deploy_pipeline": {
        "risk_tier": RiskTier.HIGH_IMPACT,
        "description": "Deploy a compiled recipe/pipeline to production or an edge execution target.",
        "examples": [
            "Deploy the sales pipeline to production",
            "Push this recipe to the edge deployment",
            "Go live with the compiled model",
        ],
        "entities": {"dataset_id": True, "recipe_name": False, "target_environment": False},
    },
    "greeting": {
        "risk_tier": RiskTier.READ_ONLY,
        "description": "A greeting or small talk with no operational request.",
        "examples": ["Hi", "Good morning", "Hello there"],
        "entities": {},
    },
    "general_help": {
        "risk_tier": RiskTier.READ_ONLY,
        "description": "The user is asking what the assistant can do, or for general guidance.",
        "examples": ["What can you help me with?", "How does this work?"],
        "entities": {},
    },
    "out_of_scope": {
        "risk_tier": RiskTier.READ_ONLY,
        "description": "The request has nothing to do with datasets, DAGs, recipes, or deployment (e.g. general knowledge questions).",
        "examples": ["What's the weather today?", "Tell me a joke"],
        "entities": {},
    },
}

VALID_INTENTS = list(INTENT_TAXONOMY.keys())


def get_risk_tier(intent_name: str) -> RiskTier:
    entry = INTENT_TAXONOMY.get(intent_name)
    if entry is None:
        return RiskTier.HIGH_IMPACT  # unknown intents are treated cautiously
    return entry["risk_tier"]


def required_entities(intent_name: str):
    entry = INTENT_TAXONOMY.get(intent_name, {})
    return [k for k, required in entry.get("entities", {}).items() if required]
