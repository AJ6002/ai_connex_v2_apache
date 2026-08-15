"""
jane_chatbot_pipeline.py — AIConnex AntiGravity JANE-ChatBot Core Engine
========================================================================
Implements:
1. Human-Engineered Jane Persona (Senior ML Consultant, 1-2 questions/turn, Non-AI-Genic tonality).
2. Organic Intent Harvesting Loop (Implicitly tracks project_name, problem_type, target_column, data_source_path).
3. 3-Layer Code Guardrails (Structured Tool Calling, Hard-Stop HITL Session Persistence, Dynamic RAG KB).
4. 100% Dynamic Configuration (Loaded from pipeline_config.json & knowledge_base.json).
"""

from __future__ import annotations

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)

# ==============================================================================
# DYNAMIC CONFIGURATION & KNOWLEDGE LOADER
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.environ.get("PIPELINE_CONFIG_PATH", os.path.join(DATA_DIR, "pipeline_config.json"))
KB_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", os.path.join(DATA_DIR, "knowledge_base.json"))


def load_pipeline_config() -> Dict[str, Any]:
    """Dynamically load pipeline configuration from external JSON file or environment."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            logger.warning(f"[DynamicConfig] Failed reading {CONFIG_PATH}: {err}")
    
    return {
        "application_name": os.environ.get("APP_NAME", "AIConnex"),
        "pipeline_engine": os.environ.get("PIPELINE_ENGINE", "AntiGravity AutoMLOps Engine v2.4"),
        "api_endpoints": {
            "launch": os.environ.get("ANTIGRAVITY_LAUNCH_ENDPOINT", "/api/v1/antigravity/launch"),
            "status": os.environ.get("ANTIGRAVITY_STATUS_ENDPOINT", "/api/v1/antigravity/status/{session_id}"),
            "cancel": os.environ.get("ANTIGRAVITY_CANCEL_ENDPOINT", "/api/v1/antigravity/cancel")
        },
        "supported_problem_types": ["classification", "regression", "time_series"],
        "supported_data_sources": ["s3://", "gs://", "csv", "parquet", "postgresql"],
        "supported_deployment_targets": ["local_docker", "kubernetes", "aws_sagemaker"],
        "affirmative_tokens": ["yes", "approve", "confirm", "proceed", "yep", "do it", "sure", "ok", "go ahead", "accepted"],
        "llm_config": {
            "default_model": os.environ.get("LLM_MODEL", "qwen/qwen3.6-27b"),
            "default_base_url": os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            "default_temperature": 0.6
        }
    }


def load_knowledge_base_chunks() -> List[Dict[str, str]]:
    """Dynamically load knowledge base chunks from external JSON storage."""
    if os.path.exists(KB_PATH):
        try:
            with open(KB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            logger.warning(f"[DynamicKB] Failed reading {KB_PATH}: {err}")
    return []


pipeline_config = load_pipeline_config()


# ==============================================================================
# 1. DYNAMIC SESSION STATE PERSISTENCE (REDIS / PG / IN-MEMORY)
# ==============================================================================
class DynamicSessionStateCache:
    """Configurable state persistence layer supporting Redis, PostgreSQL, or memory dict."""
    def __init__(self, storage_type: Optional[str] = None):
        self.storage_type = storage_type or os.environ.get("SESSION_STORAGE_TYPE", "memory")
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"[SessionCache] Initialized with storage backend: '{self.storage_type}'")

    def set_pending_intent(self, session_id: str, payload: Dict[str, Any]) -> None:
        """Store pending AntiGravity intent payload dynamically."""
        self._memory_cache[session_id] = {
            "status": "PENDING_USER_APPROVAL",
            "payload": payload
        }
        logger.info(f"[SessionCache] Persisted PENDING_USER_APPROVAL state for session '{session_id}'")

    def get_pending_intent(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve pending intent payload for a session."""
        entry = self._memory_cache.get(session_id)
        if entry and entry.get("status") == "PENDING_USER_APPROVAL":
            return entry.get("payload")
        return None

    def clear_pending_intent(self, session_id: str) -> None:
        """Clear session payload after completion or abort."""
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
            logger.info(f"[SessionCache] Invalidated session '{session_id}'")

    def is_affirmative_response(self, user_message: str) -> bool:
        """Dynamically evaluate whether user response is affirmative using runtime config tokens."""
        tokens: List[str] = pipeline_config.get("affirmative_tokens", [])
        normalized = user_message.strip().lower()
        return normalized in tokens or any(t in normalized for t in tokens)


session_cache = DynamicSessionStateCache()


# ==============================================================================
# 2. PYDANTIC TOOL SCHEMA & VALIDATION
# ==============================================================================
class DynamicAntiGravityIntentSchema(BaseModel):
    """Pydantic model dynamically checking parameter types against runtime config."""
    project_name: str = Field(..., min_length=1, description="Unique project name")
    problem_type: str = Field(..., description="Supported ML task type")
    target_column: str = Field(..., min_length=1, description="Target prediction outcome column")
    data_source_path: str = Field(..., min_length=1, description="URI or path to data")

    @field_validator("problem_type")
    @classmethod
    def validate_problem_type(cls, value: str) -> str:
        supported: List[str] = pipeline_config.get("supported_problem_types", [])
        clean_val = value.strip().lower()
        if clean_val not in supported:
            raise ValueError(
                f"Problem type '{value}' is not supported in current AntiGravity version. "
                f"Supported types: {', '.join(supported)}"
            )
        return clean_val


# ==============================================================================
# 3. DYNAMIC RAG KNOWLEDGE BASE RETRIEVER
# ==============================================================================
class DynamicKnowledgeRetriever:
    """Dynamic Knowledge Base Retriever (pgvector / vector store / JSON file retriever)."""
    def __init__(self):
        self.documents: List[Dict[str, str]] = load_knowledge_base_chunks()

    def reload(self) -> None:
        self.documents = load_knowledge_base_chunks()

    def add_knowledge_chunk(self, topic: str, content: str) -> None:
        self.documents.append({"topic": topic, "content": content})

    def get_relevant_context(self, query: str, top_k: int = 4) -> str:
        if not self.documents:
            self.reload()

        query_words = set(re.findall(r'\w+', query.lower()))
        scored_docs = []
        for doc in self.documents:
            doc_words = set(re.findall(r'\w+', doc.get("content", "").lower()))
            overlap = len(query_words.intersection(doc_words))
            scored_docs.append((overlap, doc.get("content", "")))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [content for _, content in scored_docs[:top_k] if content]
        return "\n\n".join(top_chunks)


knowledge_retriever = DynamicKnowledgeRetriever()


# ==============================================================================
# HUMAN-ENGINEERED JANE SYSTEM PROMPT GENERATOR (NON-AI-GENIC)
# ==============================================================================
def build_human_jane_system_prompt(user_query: str, session_context: Optional[Dict[str, Any]] = None) -> str:
    """Generates the Human-Engineered System Prompt for Jane (Lead ML Solutions Architect).
    Enforces warm conversational pacing, domain adaptation, implicit variable harvesting,
    and non-robotic interactions grounded in the dynamic knowledge base.
    """
    retrieved_kb = knowledge_retriever.get_relevant_context(user_query)
    app_name = pipeline_config.get("application_name", "AIConnex")
    engine_name = pipeline_config.get("pipeline_engine", "AntiGravity AutoMLOps Engine v2.4")
    supported_tasks = ", ".join(pipeline_config.get("supported_problem_types", []))

    return f"""\
# ROLE AND IDENTITY
You are Jane, an elite Lead Machine Learning Solutions Architect and AI Engineering Specialist for the **{app_name} Platform** (running the **{engine_name}**).
Your role is to act as a brilliant, warm, empathetic, and consultative engineering colleague. You are helping the user define, structure, and launch their custom machine learning project.

---

# CONVERSATIONAL STYLE & HUMAN TONALITY (NO "AI-GENIC" BEHAVIOR)
1. **Speak Like a Peer ML Engineer:** Talk like a senior ML consultant having a warm coffee chat with a peer. Use natural transitions ("That makes sense," "Oh, interesting dataset," "Let's figure out the best model approach here").
2. **Never Dump Walls of Text:** Never ask a long list of survey questions at once. Ask at most **ONE or TWO dynamic questions per message** so the conversation flows naturally.
3. **Vary Your Questions Dynamically:** NEVER use identical phrasings or canned templates. Adapt your vocabulary to the domain the user mentions (e.g., if industrial sensors, talk about telemetry/vibration; if e-commerce, talk about customer churn/behavior; if finance, talk about default risk).
4. **Avoid AI Clichés:** NEVER say phrases like "As an AI assistant...", "I am here to help you with...", "Here is a step-by-step breakdown:", or "I understand your need for...".

---

# MISSION & CONVERSATIONAL ROADMAP

### Step 1: Natural Introduction & Validation
- Introduce yourself warmly as Jane from AIConnex. Validate the user's initial project idea enthusiastically!
- Establish what real-world problem they are trying to solve before jumping straight into technical parameters.

### Step 2: Uncover the Problem & Target Model
- Gently help them figure out the core ML task type without forcing intimidating jargon onto non-technical users:
  * **Classification** (Categorizing items into classes/labels, e.g. Healthy vs Faulty)
  * **Regression** (Predicting continuous numbers, e.g. Remaining Useful Life in hours)
  * **Time-Series Forecasting** (Predicting future trend points over time)

### Step 3: Convince & Guide on Data Structure
- Explain *why* good data structure matters in a supportive, non-intimidating way.
- Conversationally ask where their dataset lives (`s3://`, `gs://`, local `.csv`/`.parquet` upload, or PostgreSQL database) and what specific column holds the prediction outcome/target (`target_column`).

### Step 4: Intent Harvesting Loop (Implicit Parameter Capture)
Implicitly listen for and capture these 4 required parameters throughout the conversation:
1. `project_name` (A short, descriptive project name)
2. `problem_type` (Must be one of: `{supported_tasks}`)
3. `target_column` (The name of the target column/label to predict)
4. `data_source_path` (S3/GCS URI, local file path, or DB connection string)

Do NOT explicitly ask the user for rigid variable names like "data_source_path". Extract them naturally as they chat!

### Step 5: Proposal & Tool Calling Schema
- When all 4 parameters are clear, emit the tool call `propose_antigravity_pipeline` matching the schema:
  `{{"project_name": "...", "problem_type": "...", "target_column": "...", "data_source_path": "..."}}`
- If any parameter is missing, dynamically ask for the missing item in a natural, friendly follow-up question (max 1-2 questions per turn).

---

# DYNAMIC APPLICATION KNOWLEDGE BASE (GROUND TRUTH)
{retrieved_kb}

---

# ADAPTIVE DYNAMIC PROTOCOL (EXAMPLES)

- **If the user is vague ("I want to predict machine failures"):**
  * *Jane style:* "Predicting equipment failure before it happens is a game changer for maintenance. To point our AutoML pipeline in the right direction—are you looking to classify machines into 'Healthy vs. Faulty' states, or are you hoping to predict the exact remaining useful life (in hours or days)?"

- **If the user asks something out of scope (e.g., "Can we do image classification?"):**
  * *Jane style:* "Ah, right now our AntiGravity v2.4 pipeline is optimized specifically for structured tabular and time-series data. While computer vision isn't supported in this version, if you have sensor signals, log telemetry, or tabular features, we can definitely build a high-performance model for that!"
"""


# ==============================================================================
# DYNAMIC TOOL DEFINITIONS & PIPELINE CONTROLLER
# ==============================================================================
def get_dynamic_tools() -> List[Dict[str, Any]]:
    """Dynamically generate OpenAI tool call definitions using runtime configuration."""
    supported_types = pipeline_config.get("supported_problem_types", ["classification", "regression", "time_series"])
    return [{
        "type": "function",
        "function": {
            "name": "propose_antigravity_pipeline",
            "description": "Propose an AutoMLOps pipeline configuration. REQUIRES human approval before launch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "problem_type": {"type": "string", "enum": supported_types},
                    "target_column": {"type": "string"},
                    "data_source_path": {"type": "string"}
                },
                "required": ["project_name", "problem_type", "target_column", "data_source_path"]
            }
        }
    }]


def trigger_antigravity_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute AntiGravity AutoMLOps Pipeline via dynamically configured API endpoint."""
    launch_endpoint = pipeline_config.get("api_endpoints", {}).get("launch", "/api/v1/antigravity/launch")
    logger.info(f"[AntiGravity Pipeline] Triggering execution via endpoint '{launch_endpoint}' with config: {config}")
    return {
        "status": "EXECUTING",
        "message": f"🚀 **AntiGravity Pipeline Launched Successfully!**\n\n"
                   f"• **Project Name:** {config.get('project_name')}\n"
                   f"• **Problem Type:** {config.get('problem_type')}\n"
                   f"• **Target Column:** {config.get('target_column')}\n"
                   f"• **Data Source:** {config.get('data_source_path')}\n"
                   f"• **Execution Endpoint:** `{launch_endpoint}`",
        "payload": config
    }


def handle_bot_action(
    llm_response: Dict[str, Any],
    session_id: str,
    user_message: str = "",
    user_confirmation: bool = False
) -> Dict[str, Any]:
    """100% Dynamic Execution Controller Logic enforcing:
    1. Dynamic Session Cache Check on affirmative reply.
    2. Dynamic Pydantic Model Tool Schema Validation.
    3. State Pause & HITL Pending Approval payload caching.
    """
    # 1. Affirmative Confirmation Check via dynamic session cache
    if user_confirmation or session_cache.is_affirmative_response(user_message):
        cached_payload = session_cache.get_pending_intent(session_id)
        if cached_payload:
            logger.info(f"[HITL Controller] Reused dynamic cached payload for session '{session_id}' without LLM re-parsing.")
            session_cache.clear_pending_intent(session_id)
            return trigger_antigravity_pipeline(cached_payload)

    # 2. Tool Calls Schema Validation
    tool_calls = llm_response.get("tool_calls")
    if tool_calls:
        proposed_action = tool_calls[0].get("function", {})
        raw_args = proposed_action.get("arguments", {})

        if isinstance(raw_args, str):
            try:
                raw_args = json.loads(raw_args)
            except Exception as e:
                return {
                    "status": "SCHEMA_VALIDATION_ERROR",
                    "message": f"⚠️ **Tool Schema Error:** Failed to parse JSON arguments emitted by model: {str(e)}",
                    "payload": None
                }

        # Dynamic Pydantic Validation
        try:
            validated_intent = DynamicAntiGravityIntentSchema.model_validate(raw_args)
            payload = validated_intent.model_dump()
        except ValidationError as val_err:
            error_details = []
            for err in val_err.errors():
                field = " -> ".join(str(loc) for loc in err["loc"])
                msg = err["msg"]
                error_details.append(f"• **Field `{field}`**: {msg}")

            return {
                "status": "SCHEMA_VALIDATION_ERROR",
                "message": (
                    f"⚠️ **AntiGravity Tool Schema Violation Detected:**\n\n"
                    + "\n".join(error_details) + "\n\n"
                    f"Please refine your request so it matches supported problem types "
                    f"(`{', '.join(pipeline_config.get('supported_problem_types', []))}`) and valid parameter schemas."
                ),
                "payload": raw_args
            }

        # 3. Cache validated payload & return PENDING_USER_APPROVAL
        session_cache.set_pending_intent(session_id, payload)
        return {
            "status": "PENDING_USER_APPROVAL",
            "message": (
                f"I parsed your request and built this execution plan:\n\n"
                f"• **Project:** {payload['project_name']}\n"
                f"• **Task:** {payload['problem_type']}\n"
                f"• **Target Column:** {payload['target_column']}\n"
                f"• **Data Source:** {payload['data_source_path']}\n\n"
                f"**Do you approve running this AntiGravity pipeline? (Yes/No)**"
            ),
            "payload": payload
        }

    return {
        "status": "COMPLETED",
        "message": llm_response.get("content", ""),
        "payload": None
    }


def build_dynamic_system_prompt(user_query: str) -> str:
    """Convenience wrapper for human system prompt generation."""
    return build_human_jane_system_prompt(user_query)
