"""
Extraction layer: turns a free-text prompt (+ conversation history) into a
structured ExtractedIntent (intent, entities, confidence) using an LLM's
structured-output mode.

If GEMINI_API_KEY isn't configured, falls back to a tiny keyword-based
simulator so the rest of the backend can be built/tested without a live key
-- mirrors the fallback pattern already used in the Node server.ts.
"""

import json
import os
import re

from intents import INTENT_TAXONOMY, VALID_INTENTS
from schemas import ExtractedIntent

GEMINI_MODEL = "gemini-3.6-flash"


def _build_system_prompt() -> str:
    intent_lines = []
    for name, spec in INTENT_TAXONOMY.items():
        examples = "; ".join(spec["examples"][:3])
        intent_lines.append(f'- "{name}": {spec["description"]} Examples: {examples}')

    return (
        "You are the intent-and-entity extraction layer for the AI Connexx "
        "assistant, part of the TAS AI-Connexx Suite for ML model validation.\n\n"
        "Given the user's message and conversation history, identify:\n"
        "1. Which ONE intent from the list below best matches the message.\n"
        "2. Any entities mentioned: dataset_id, dag_id, recipe_name, target_environment.\n"
        "3. A confidence score between 0 and 1 for your intent choice.\n\n"
        "Valid intents:\n" + "\n".join(intent_lines) + "\n\n"
        "If nothing matches well, use \"out_of_scope\".\n"
        "Respond with ONLY a JSON object of this exact shape, no other text:\n"
        '{"intent": "...", "entities": {"dataset_id": null, "dag_id": null, '
        '"recipe_name": null, "target_environment": null}, "confidence": 0.0, '
        '"reasoning": "..."}'
    )


def _call_gemini(message: str, history: list) -> str:
    """Calls Gemini with structured-output config and returns the raw JSON text."""
    from google import genai  # imported lazily so the fallback path works without the package installed

    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    contents = []
    for turn in history or []:
        role = "user" if turn.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": turn.get("text", "")}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config={
            "system_instruction": _build_system_prompt(),
            "temperature": 0.1,  # low temperature: this is a classification task, not creative generation
            "response_mime_type": "application/json",
        },
    )
    return response.text


def _fallback_extract(message: str) -> dict:
    """Simple keyword-based simulator used only when no API key is configured,
    so the pipeline can be built and tested end-to-end without a live key."""
    text = message.lower()

    dataset_match = re.search(r"\b([a-z0-9_\-]+\.(csv|json|xml)|[a-z0-9_\-]*dataset[a-z0-9_\-]*)\b", text)
    dataset_id = dataset_match.group(0) if dataset_match else None

    strong_match = True  # whether a fairly unambiguous keyword rule fired

    if any(g in text for g in ["hi", "hello", "good morning", "hey"]) and len(text.split()) <= 4:
        intent = "greeting"
    elif "help" in text or "what can you" in text:
        intent = "general_help"
    elif "deploy" in text or "production" in text or "go live" in text:
        intent = "deploy_pipeline"
    elif "compile" in text or ("recipe" in text and ("run" in text or "generate" in text or "compile" in text)):
        intent = "compile_training_recipe"
    elif "recipe" in text and ("status" in text or "what" in text or "check" in text):
        intent = "get_recipe_status"
    elif "dag" in text and ("run" in text or "verify" in text or "kick off" in text):
        intent = "run_dag_verification"
    elif "dag" in text and ("status" in text or "what" in text or "check" in text):
        intent = "get_dag_status"
    elif "profile" in text and "dataset" in text:
        intent = "run_dataset_profiling"
    elif "status" in text or "score" in text or "check" in text:
        intent = "get_dataset_status"
    else:
        intent = "out_of_scope"
        strong_match = False

    # Intents that don't need a dataset_id can still be high-confidence
    # without one; intents that do need one are penalized if it's missing.
    needs_dataset = intent not in ("greeting", "general_help", "out_of_scope")
    if not strong_match:
        confidence = 0.3
    elif needs_dataset and not dataset_id:
        confidence = 0.55
    else:
        confidence = 0.9

    return {
        "intent": intent,
        "entities": {"dataset_id": dataset_id, "dag_id": None, "recipe_name": None, "target_environment": None},
        "confidence": confidence,
        "reasoning": "fallback keyword simulator (no GEMINI_API_KEY configured)",
    }


def extract_intent(message: str, history: list) -> ExtractedIntent:
    """Main entry point: returns a validated ExtractedIntent."""
    if os.environ.get("GEMINI_API_KEY"):
        try:
            raw_text = _call_gemini(message, history)
            parsed = json.loads(raw_text)
        except Exception as exc:  # network error, bad JSON, missing package, etc.
            parsed = _fallback_extract(message)
            parsed["reasoning"] = f"fallback used after extraction error: {exc}"
    else:
        parsed = _fallback_extract(message)

    return ExtractedIntent.model_validate(parsed)
