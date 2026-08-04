"""
Extraction layer for the pre-upload conversation phase.

Turns a user message (+ current contract state + history) into a
TurnExtraction — only the fields the LLM found new or updated information
for, each with its own confidence score.

Mirrors the pattern in extraction.py: uses Gemini structured-output mode
when a key is configured, falls back to a keyword-based simulator otherwise.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from pre_upload_schemas import TurnExtraction, PreUploadContract, CandidateMLProblemType
from pre_upload_config import get_all_tiered_fields


def _build_system_prompt(contract: PreUploadContract) -> str:
    """Build a system prompt that includes the current contract state
    so the LLM knows what's already been established."""

    # Describe the fields the LLM should extract
    field_descriptions = []
    for entry in get_all_tiered_fields():
        field_descriptions.append(f'- "{entry.path}" (confidence field: "{entry.confidence_field}")')

    current_state = contract.model_dump_json(indent=2)

    return (
        "You are the pre-upload intent-gathering layer for the AIConnex assistant.\n\n"
        "Your job is to read the user's latest message (plus conversation history) and "
        "extract ONLY the fields where you find NEW or UPDATED information. Do NOT "
        "restate the entire contract — only return what changed this turn.\n\n"
        "For each field you populate, you MUST also provide a confidence score "
        "(0.0 to 1.0) in the corresponding confidence field. Be conservative:\n"
        "- 0.9+ if the user explicitly stated it\n"
        "- 0.6-0.8 if you can infer it with reasonable certainty\n"
        "- 0.4-0.5 if it's a weak signal\n"
        "- Leave null / 0.0 if you have no information\n\n"
        "Fields you can extract:\n"
        + "\n".join(field_descriptions) + "\n\n"
        "Current contract state (what's already known):\n"
        f"{current_state}\n\n"
        "Respond with ONLY a JSON object matching the TurnExtraction schema, no other text. "
        "Include ONLY fields that changed this turn. Set confidence to 0.0 for fields "
        "you're not updating."
    )


def _get_api_key() -> str:
    key_path = r"C:\Users\tasoman\Documents\key.txt"
    if os.path.exists(key_path):
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return os.environ.get("OPENROUTER_API_KEY") or os.environ.get("QWEN_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""


def _call_qwen(
    message: str,
    history: list,
    contract: PreUploadContract,
    api_key: str,
) -> str:
    """Call OpenRouter Qwen with structured-output mode and return raw JSON text."""
    from openai import OpenAI

    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.environ.get("LLM_MODEL", "qwen/qwen-2.5-coder-32b-instruct")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=10.0,
    )

    messages = [{"role": "system", "content": _build_system_prompt(contract)}]
    for turn in history or []:
        role = "user" if turn.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": turn.get("text", "")})
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1,
        max_tokens=250,
    )
    return response.choices[0].message.content



def _fallback_extract(message: str, contract: PreUploadContract) -> dict:
    """Keyword-based fallback simulator for the pre-upload extraction.
    Mirrors the pattern in extraction.py's _fallback_extract."""
    text = message.lower()

    result: dict = {
        # Goal fields
        "primary_goal": None,
        "primary_goal_confidence": 0.0,
        "secondary_goals": None,
        "secondary_goals_confidence": 0.0,
        "business_problem": None,
        "business_problem_confidence": 0.0,
        "candidate_ml_problem_types": None,
        "candidate_ml_problem_types_confidence": 0.0,
        # Observed
        "industry_terms": None,
        "equipment": None,
        "assets": None,
        "datasets_mentioned": None,
        "locations": None,
        "time_periods": None,
        "quantities": None,
        "keywords": None,
        "user_statements": None,
        # Inferred
        "industry": None,
        "industry_confidence": 0.0,
        "user_role": None,
        "user_role_confidence": 0.0,
        "business_domain": None,
        "business_domain_confidence": 0.0,
        "experience_level": None,
        "experience_level_confidence": 0.0,
        # Dataset expectation
        "expected_file_types": None,
        "expected_file_types_confidence": 0.0,
        "expected_dataset_type": None,
        "expected_dataset_type_confidence": 0.0,
        "expected_duration": None,
        "expected_duration_confidence": 0.0,
        "expected_sampling_rate": None,
        "expected_sampling_rate_confidence": 0.0,
        "expected_size": None,
        "expected_size_confidence": 0.0,
        # Constraints
        "preferred_algorithms": None,
        "preferred_frameworks": None,
        "explainability_required": None,
        "explainability_required_confidence": 0.0,
        "deployment_constraints": None,
        "business_constraints": None,
        "technical_constraints": None,
        # Conversation analysis
        "urgency": None,
        "urgency_confidence": 0.0,
        "sentiment": None,
        "certainty_level": None,
        "ambiguity_detected": None,
        # Planning
        "recommended_next_action": None,
        "wait_for_dataset": None,
    }

    # --- Goal detection ---
    # Primary goal: look for phrases like "I want to", "I need to", "my goal is"
    goal_patterns = [
        (r"(?:i\s+(?:want|need|would\s+like)\s+to\s+)(.+?)(?:\.|$)", 0.85),
        (r"(?:my\s+(?:goal|objective|aim)\s+(?:is\s+)?to\s+)(.+?)(?:\.|$)", 0.9),
        (r"(?:i['']?m\s+(?:trying|looking)\s+to\s+)(.+?)(?:\.|$)", 0.8),
        (r"(?:predict|forecast|classify|detect|analyze|optimize)\s+(.+?)(?:\.|$)", 0.7),
    ]
    for pattern, conf in goal_patterns:
        m = re.search(pattern, text)
        if m:
            result["primary_goal"] = m.group(1).strip()
            result["primary_goal_confidence"] = conf
            break

    # ML problem types
    ml_types = []
    ml_keywords = {
        "regression": 0.9, "classification": 0.9, "clustering": 0.9,
        "anomaly detection": 0.9, "forecasting": 0.85, "prediction": 0.8,
        "time series": 0.85, "segmentation": 0.8, "ranking": 0.8,
        "recommendation": 0.85, "nlp": 0.8, "computer vision": 0.8,
    }
    for kw, conf in ml_keywords.items():
        if kw in text:
            ml_types.append({"type": kw, "confidence": conf})
    if ml_types:
        result["candidate_ml_problem_types"] = ml_types
        result["candidate_ml_problem_types_confidence"] = max(c["confidence"] for c in ml_types)

    # --- Dataset expectation ---
    file_type_patterns = [
        (r"\.csv\b", "CSV"), (r"\.json\b", "JSON"), (r"\.xml\b", "XML"),
        (r"\.parquet\b", "Parquet"), (r"\.avro\b", "Avro"), (r"\.zip\b", "ZIP"),
        (r"\bcsv\b", "CSV"), (r"\bexcel\b", "Excel"), (r"\bjson\b", "JSON"),
        (r"\bzip\b", "ZIP"), (r"\barchive\b", "ZIP"), (r"\btar\b", "TAR"),
    ]
    file_types = []
    for pat, ftype in file_type_patterns:
        if re.search(pat, text):
            file_types.append(ftype)
    if file_types:
        result["expected_file_types"] = list(set(file_types))
        result["expected_file_types_confidence"] = 0.85

    dataset_type_keywords = {
        "time-series": 0.85, "time series": 0.85, "timeseries": 0.85, "tabular": 0.8,
        "sensor": 0.8, "image": 0.85, "text": 0.8, "audio": 0.8,
        "video": 0.8, "signal": 0.8,
    }
    for kw, conf in dataset_type_keywords.items():
        if kw in text:
            result["expected_dataset_type"] = "time_series" if "time" in kw else kw
            result["expected_dataset_type_confidence"] = conf
            break


    # Duration
    duration_patterns = [
        (r"(\d+\s*(?:year|month|week|day|hour|minute|second)s?)", 0.8),
    ]
    for pat, conf in duration_patterns:
        m = re.search(pat, text)
        if m:
            result["expected_duration"] = m.group(1)
            result["expected_duration_confidence"] = conf
            break

    # Size
    size_patterns = [
        (r"(\d+\s*(?:gb|mb|kb|tb|gigabyte|megabyte))", 0.8),
        (r"(\d+\s*(?:million|thousand)\s*(?:rows|records|samples))", 0.8),
    ]
    for pat, conf in size_patterns:
        m = re.search(pat, text)
        if m:
            result["expected_size"] = m.group(1)
            result["expected_size_confidence"] = conf
            break

    # --- Inferred ---
    industry_keywords = {
        "manufacturing": 0.8, "energy": 0.8, "oil": 0.8, "gas": 0.8,
        "healthcare": 0.8, "medical": 0.8, "finance": 0.8, "banking": 0.8,
        "retail": 0.8, "ecommerce": 0.8, "automotive": 0.8, "aerospace": 0.8,
        "telecom": 0.8, "logistics": 0.8, "supply chain": 0.8,
        "pharma": 0.8, "biotech": 0.8,
    }
    for kw, conf in industry_keywords.items():
        if kw in text:
            result["industry"] = kw
            result["industry_confidence"] = conf
            break

    role_keywords = {
        "data scientist": 0.85, "engineer": 0.7, "analyst": 0.8,
        "researcher": 0.7, "manager": 0.7, "technician": 0.7,
        "operator": 0.7, "scientist": 0.7,
    }
    for kw, conf in role_keywords.items():
        if kw in text:
            result["user_role"] = kw
            result["user_role_confidence"] = conf
            break

    # --- Constraints ---
    if any(w in text for w in ["explainable", "explainability", "interpretable", "why"]):
        result["explainability_required"] = True
        result["explainability_required_confidence"] = 0.8

    # --- Conversation analysis ---
    if any(w in text for w in ["urgent", "asap", "immediately", "critical", "emergency"]):
        result["urgency"] = "high"
        result["urgency_confidence"] = 0.8
    elif any(w in text for w in ["soon", "priority", "important"]):
        result["urgency"] = "medium"
        result["urgency_confidence"] = 0.7
    else:
        result["urgency"] = "normal"
        result["urgency_confidence"] = 0.6

    # Sentiment
    positive_words = ["great", "good", "excellent", "thanks", "help", "please"]
    negative_words = ["bad", "terrible", "awful", "broken", "issue", "problem", "error", "fail"]
    if any(w in text for w in negative_words):
        result["sentiment"] = "negative"
    elif any(w in text for w in positive_words):
        result["sentiment"] = "positive"
    else:
        result["sentiment"] = "neutral"

    # Ambiguity detection: short messages, vague words
    word_count = len(text.split())
    vague_words = ["thing", "stuff", "something", "data", "it", "that", "this", "things"]
    if word_count <= 3 or (any(w in text for w in vague_words) and word_count <= 6):
        result["ambiguity_detected"] = True
    else:
        result["ambiguity_detected"] = False

    # --- Observed ---
    # Keywords
    observed_keywords = re.findall(r"\b([a-z]{4,})\b", text)
    if observed_keywords:
        result["keywords"] = list(set(observed_keywords[:10]))

    # User statements (the raw message as a statement)
    if message.strip():
        result["user_statements"] = [message.strip()]

    # Equipment
    equipment_keywords = ["sensor", "machine", "equipment", "motor", "pump", "valve",
                          "conveyor", "robot", "actuator", "drill", "turbine", "generator"]
    found_equipment = [w for w in equipment_keywords if w in text]
    if found_equipment:
        result["equipment"] = found_equipment

    # Locations
    location_pattern = r"(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
    loc_matches = re.findall(location_pattern, message)
    if loc_matches:
        result["locations"] = loc_matches[:3]

    # Time periods
    time_patterns = [
        r"(last\s+\d+\s+(?:year|month|week|day|quarter)s?)",
        r"(next\s+\d+\s+(?:year|month|week|day|quarter)s?)",
        r"(\d{4})\s*[-–to]+\s*(\d{4})",
        r"(Q[1-4]\s*\d{4})",
    ]
    time_matches = []
    for pat in time_patterns:
        m = re.search(pat, text)
        if m:
            time_matches.append(m.group(0))
    if time_matches:
        result["time_periods"] = time_matches[:3]

    # Quantities
    qty_pattern = r"(\d[\d,]*\.?\d*\s*(?:records|rows|samples|files|datasets|gb|mb|tb|hours|days|months))"
    qty_matches = re.findall(qty_pattern, text)
    if qty_matches:
        result["quantities"] = qty_matches[:3]

    return result


def _clean_json_text(text: str) -> str:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def extract_pre_upload_turn(
    message: str,
    history: list,
    contract: PreUploadContract,
) -> TurnExtraction:
    """Main entry point: returns a TurnExtraction for this turn."""
    clean_text = message.strip().lower()

    # Optimization 2: Short-circuit simple greetings to avoid unnecessary 2,000-token LLM extraction
    if clean_text in ("hi", "hello", "hey", "greetings", "good morning") or (
        len(clean_text.split()) <= 3 and any(w in clean_text for w in ["hi", "hello", "hey"])
    ):
        return TurnExtraction()

    api_key = _get_api_key()
    if api_key and os.environ.get("FORCE_KEYWORD_FALLBACK") != "true":
        try:
            raw_text = _call_qwen(message, history, contract, api_key)
            cleaned = _clean_json_text(raw_text)
            parsed = json.loads(cleaned)
        except Exception as exc:
            parsed = _fallback_extract(message, contract)
            parsed["reasoning"] = f"fallback used after extraction error: {exc}"
    else:
        parsed = _fallback_extract(message, contract)

    return TurnExtraction.model_validate(parsed)