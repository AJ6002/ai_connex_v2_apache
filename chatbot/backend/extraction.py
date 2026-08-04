"""
Extraction layer: turns a free-text prompt (+ conversation history) into a
structured ExtractedIntent (intent, entities, confidence) using an LLM's
structured-output mode.

If no key is configured or on network timeout, falls back to keyword-based simulator.
"""

import json
import os
import re

from intents import INTENT_TAXONOMY, VALID_INTENTS
from schemas import ExtractedIntent, ExtractedEntities



def _build_system_prompt() -> str:
    taxonomy_desc = []
    for name, info in INTENT_TAXONOMY.items():
        taxonomy_desc.append(
            f"- {name} ({info['risk_tier'].value}): {info['description']}\n"
            f"  Examples: {', '.join(info['examples'])}"
        )

    return (
        "You are the intent-recognition layer for the AIConnex chatbot.\n\n"
        "Analyze the user's message (+ history) and extract:\n"
        "1. intent: one of [" + ", ".join(VALID_INTENTS) + "]\n"
        "2. confidence: float between 0.0 and 1.0\n"
        "3. entities: dataset_id, dag_id, recipe_name, target_environment\n\n"
        "Intents taxonomy:\n" + "\n".join(taxonomy_desc) + "\n\n"
        "Respond with ONLY a JSON object: "
        '{"confidence": 0.95, "intent": "<intent_name>", "entities": {"dataset_id": null, "dag_id": null, "recipe_name": null, "target_environment": null}}'
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


def _call_qwen(message: str, history: list, api_key: str) -> str:
    """Calls OpenRouter Qwen with structured-output config, 10s timeout, and 250 max_tokens."""
    from openai import OpenAI

    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.environ.get("LLM_MODEL", "qwen/qwen-2.5-coder-32b-instruct")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=10.0,
    )

    messages = [{"role": "system", "content": _build_system_prompt()}]
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


def _fallback_extract(message: str) -> dict:
    """Simple keyword-based simulator used when LLM call times out or fails."""
    text = message.lower()

    dataset_match = re.search(r"\b([a-z0-9_\-]+\.(csv|json|xml))\b", text)
    if not dataset_match:
        dataset_match = re.search(r"\b([a-z0-9_\-]*dataset[a-z0-9_\-]*)\b", text)
    dataset_id = dataset_match.group(0) if dataset_match else None

    strong_match = True

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
        "reasoning": "fallback keyword simulator",
    }


def _clean_json_text(text: str) -> str:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def extract_intent(message: str, history: list) -> ExtractedIntent:
    """Main entry point: returns a validated ExtractedIntent."""
    clean_text = message.strip().lower()

    # Optimization 2: Short-circuit simple greetings to avoid unnecessary 2,000-token LLM extraction
    if clean_text in ("hi", "hello", "hey", "greetings", "good morning") or (
        len(clean_text.split()) <= 3 and any(w in clean_text for w in ["hi", "hello", "hey"])
    ):
        return ExtractedIntent(
            intent="greeting",
            confidence=0.95,
            entities=ExtractedEntities(),
            reasoning="Fast short-circuit for greeting phrase",
        )


    api_key = _get_api_key()
    if api_key and os.environ.get("FORCE_KEYWORD_FALLBACK") != "true":
        try:
            raw_text = _call_qwen(message, history, api_key)
            cleaned = _clean_json_text(raw_text)
            parsed = json.loads(cleaned)
        except Exception as exc:
            parsed = _fallback_extract(message)
            parsed["reasoning"] = f"fallback used after extraction error: {exc}"
    else:
        parsed = _fallback_extract(message)

    return ExtractedIntent.model_validate(parsed)
