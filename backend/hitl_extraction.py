"""
hitl_extraction.py — Dataset-driven HITL extraction (Task 1, v2).

Replaces the previous ETP-hardcoded system prompt with a fully dynamic
`build_hitl_system_prompt(dic_context)` that constructs the LLM instructions
from Scout's actual Recipe Catalog / dataset identity / schema map. The LLM
is still the primary intelligence; it now just receives instructions grounded
in the real uploaded dataset instead of a fixed wastewater test scenario.

  - Builds a dataset-aware system prompt from DIC context (recipes, schema,
    identity, feature catalog).
  - Calls Qwen 32B (OpenRouter) to extract structured HITLTurnExtraction JSON.
  - Falls back to recipe-aware keyword heuristics if the API is unavailable —
    parses numeric / letter picks against the actual recipe list, not against
    a hardcoded TDS/COD/hybrid keyword set.
"""

from __future__ import annotations

import json
import logging
import os
import re

from hitl_schemas import HITLContract, HITLTurnExtraction

logger = logging.getLogger(__name__)


# ─── Dynamic system prompt (built per session from the real DIC) ──────────────

_BASE_SYSTEM_INSTRUCTIONS = """\
You are a conversational assistant for AIConnex. Your job is to help the user
(a domain expert, NOT a data scientist) pick the right analytical objective
for their dataset and specify any follow-up preferences needed to configure
the training pipeline.

═══════════════════════════════════════════════════════
YOUR TASK: HITL RECIPE SELECTION
═══════════════════════════════════════════════════════

1. Look at the DATASET CONTEXT and RECIPE CATALOG below.
2. Ask the user which recipe (analytical objective) they want to pursue.
3. Once they pick one, ask ONE follow-up question at a time if the recipe
   type has natural operational preferences worth capturing (e.g. forecast
   horizon for regression, alert sensitivity for anomaly detection, display
   format for dashboards). Skip follow-ups for recipes that have no
   meaningful operational refinements — no need to invent them.
4. When you have enough information, set hitl_complete=true and write a
   short confirmation summary.

RULES:
  • Speak in plain, domain-appropriate English. NEVER say "target column",
    "DAG", "algorithm", "hyperparameter", or other data-science jargon.
  • Ask ONE question per turn. Never dump multiple questions at once.
  • Refer to columns / entities by the names actually present in the dataset,
    not made-up examples.
  • If the user's answer is unclear, gently re-present the numbered options.
  • Follow-up preferences are OPTIONAL. If the recipe has no obvious
    operational refinements needed, set hitl_complete=true immediately
    after the recipe is picked.

═══════════════════════════════════════════════════════
OUTPUT FORMAT (STRICT — JSON only, no other text)
═══════════════════════════════════════════════════════
Return a JSON object with these fields:
{
  "selected_recipe_id": "<recipe id from catalog, e.g. R001 | null>",
  "selected_recipe_confidence": <0.0-1.0>,
  "operational_preferences": { <recipe-specific k/v, e.g. "forecast_horizon_days": 7> },
  "success_metrics": [ "<any success criteria user stated>" ],
  "reply": "<your warm, plain-English conversational reply to show the user>",
  "hitl_complete": <true|false>
}

Only populate fields that CHANGED this turn. Leave others null / 0.0 / empty.
The "reply" field is what the terminal will print to the user.
"""


def _summarise_recipes(recipes: list) -> str:
    if not recipes:
        return "  (No recipes were produced by Scout for this dataset — ask the user to describe their goal in their own words.)"
    lines = []
    for r in recipes:
        rid = r.get("id", "?")
        title = r.get("title", "Untitled")
        task = r.get("task", "?")
        conf = r.get("confidence", 1.0)
        target = r.get("target") or "(no explicit target)"
        rationale = (r.get("rationale") or "").strip()
        lines.append(
            f"  • {rid} — {title}  [task={task}, target={target}, confidence={conf:.2f}]"
        )
        if rationale:
            lines.append(f"      rationale: {rationale}")
    return "\n".join(lines)


def _summarise_schema(dic_context: dict, max_columns: int = 15) -> str:
    schema_map = dic_context.get("schema_map") or {}
    if not schema_map:
        return "  (No schema information available.)"
    items = list(schema_map.items())[:max_columns]
    lines = [f"  • {col}: {dtype}" for col, dtype in items]
    if len(schema_map) > max_columns:
        lines.append(f"  … and {len(schema_map) - max_columns} more columns")
    return "\n".join(lines)


def build_hitl_system_prompt(dic_context: dict) -> str:
    """Construct the LLM system prompt from Scout's actual DIC output.

    Nothing in the returned string is hardcoded per domain — every dataset
    identity, column name, and recipe listed comes from what Scout genuinely
    discovered for the uploaded file.
    """
    dic_context = dic_context or {}
    identity = dic_context.get("dataset_identity") or {}
    compiled = dic_context.get("compiled_dataset") or {}
    recipes = dic_context.get("recipes") or []
    target_candidates = dic_context.get("target_candidates") or []

    name = identity.get("name") or "your dataset"
    domain = identity.get("domain") or identity.get("family") or "unknown domain"
    rows = compiled.get("rows") or compiled.get("row_count") or "?"
    columns = compiled.get("columns") or compiled.get("column_count") or "?"

    dataset_block = (
        "═══════════════════════════════════════════════════════\n"
        "DATASET CONTEXT (compiled by Scout — do not re-ask about it)\n"
        "═══════════════════════════════════════════════════════\n"
        f"Name:    {name}\n"
        f"Domain:  {domain}\n"
        f"Rows:    {rows}\n"
        f"Columns: {columns}\n"
        f"Target candidates (Scout-detected): {', '.join(target_candidates) if target_candidates else '(none flagged)'}\n"
        "\nColumn schema (top slice):\n"
        f"{_summarise_schema(dic_context)}\n"
    )

    recipes_block = (
        "═══════════════════════════════════════════════════════\n"
        "RECIPE CATALOG (Scout-generated — the user picks ONE)\n"
        "═══════════════════════════════════════════════════════\n"
        f"{_summarise_recipes(recipes)}\n"
    )

    return _BASE_SYSTEM_INSTRUCTIONS + "\n" + dataset_block + "\n" + recipes_block


# ─── API key helper (unchanged) ───────────────────────────────────────────────

def _get_api_key() -> str:
    key_path = r"C:\Users\tasoman\Documents\key.txt"
    if os.path.exists(key_path):
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return (
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("QWEN_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    )


# ─── LLM call (now takes dic_context, builds prompt dynamically) ─────────────

def _call_llm(
    message: str,
    history: list[dict],
    contract: HITLContract,
    dic_context: dict,
    api_key: str,
) -> str:
    """Call LLM for HITL extraction. Primary: Tier 1 Local LLM; Fallback: Tier 2 OpenRouter API."""
    # 1. Primary Intent: Tier 1 Local Offline LLM
    try:
        from local_gguf_runner import generate_local_gguf_response
        local_reply = generate_local_gguf_response(
            user_prompt=message,
            context={"history": history, "dic_context": dic_context},
            model_key="qwen2.5-coder-3b-q4"
        )
        if local_reply and len(local_reply.strip()) > 5 and ("{" in local_reply or "selected_recipe_id" in local_reply):
            return local_reply.strip()
    except Exception:
        pass

    # 2. Fallback Intent: Tier 2 OpenRouter API
    from openai import OpenAI

    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model    = os.environ.get("LLM_MODEL", "qwen/qwen-2.5-coder-32b-instruct")

    system_prompt = build_hitl_system_prompt(dic_context)

    # Inject current contract state so the LLM knows what has already been captured.
    prefs_summary = (
        ", ".join(f"{k}={v}" for k, v in contract.operational_preferences.items())
        if contract.operational_preferences
        else "(none captured yet)"
    )
    contract_summary = (
        "\nCURRENT HITL STATE (already answered — do not re-ask):\n"
        f"  selected_recipe_id:       {contract.selected_recipe_id or 'NOT YET SELECTED'}\n"
        f"  operational_preferences:  {prefs_summary}\n"
        f"  success_metrics:          {contract.success_metrics or '(none stated)'}\n"
    )

    messages = [{"role": "system", "content": system_prompt + contract_summary}]

    for turn in history or []:
        role = "user" if turn.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": turn.get("content", "")})

    messages.append({"role": "user", "content": message})

    if not api_key:
        return "{}"

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=12.0)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


# ─── JSON parse helper (unchanged) ────────────────────────────────────────────

def _parse_llm_json(raw: str) -> dict:
    """Extract JSON from LLM output (handles markdown code fences)."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if match:
        raw = match.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        brace_match = re.search(r"\{[\s\S]+\}", raw)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except Exception:
                pass
    logger.warning(f"[HITLExtraction] Could not parse LLM JSON:\n{raw}")
    return {}


# ─── Recipe-aware keyword fallback (no ETP hardcoding) ────────────────────────

def _format_recipe_menu(recipes: list) -> str:
    """Numbered recipe menu shown when we need to re-prompt the user."""
    if not recipes:
        return (
            "I couldn't automatically derive analytical objectives for this dataset. "
            "Could you describe in one sentence what you'd like to accomplish with it?"
        )
    lines = ["Which analytical objective would you like to pursue?\n"]
    for i, r in enumerate(recipes, start=1):
        title = r.get("title", f"Recipe {i}")
        task = r.get("task", "")
        target = r.get("target")
        target_str = f" — target: {target}" if target else ""
        lines.append(f"  [{i}] {title}  ({task}{target_str})")
    lines.append("\nPlease reply with the number (e.g. 1, 2, 3) or the objective name.")
    return "\n".join(lines)


_LETTER_MAP = {c: i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}


def _resolve_recipe_pick(message: str, recipes: list) -> tuple[str | None, float]:
    """Best-effort recipe id + confidence from a raw user message. Returns
    (None, 0.0) if we can't confidently decide from keywords alone."""
    if not recipes:
        return None, 0.0
    text = message.lower().strip()

    # Numeric pick: "1", "2", "recipe 3", etc.
    num_match = re.search(r"\b(\d+)\b", text)
    if num_match:
        idx = int(num_match.group(1)) - 1
        if 0 <= idx < len(recipes):
            return recipes[idx].get("id"), 0.9

    # Letter pick: "A", "B", "C"
    letter_match = re.match(r"^\s*([a-z])\s*(?:[).:\-]|$)", text)
    if letter_match:
        idx = _LETTER_MAP.get(letter_match.group(1))
        if idx is not None and idx < len(recipes):
            return recipes[idx].get("id"), 0.85

    # Recipe-id direct hit ("R001", "R002")
    id_match = re.search(r"\b([Rr]\d{2,4})\b", message)
    if id_match:
        rid = id_match.group(1).upper()
        for r in recipes:
            if str(r.get("id", "")).upper() == rid:
                return r.get("id"), 0.95

    # Title fuzzy match: any recipe whose title has >=2 salient words in the text
    for r in recipes:
        title_words = [w for w in re.findall(r"[a-zA-Z]{4,}", (r.get("title") or "").lower())]
        if not title_words:
            continue
        hits = sum(1 for w in title_words if w in text)
        if hits >= max(2, len(title_words) // 2):
            return r.get("id"), 0.7

    return None, 0.0


def _fallback_extract(
    message: str,
    contract: HITLContract,
    dic_context: dict,
) -> dict:
    """Recipe-aware fallback used when the LLM is unavailable. Purely
    deterministic, no ETP keywords."""
    recipes = (dic_context or {}).get("recipes") or []

    result: dict = {
        "selected_recipe_id": None,
        "selected_recipe_confidence": 0.0,
        "operational_preferences": {},
        "success_metrics": [],
        "reply": "",
        "hitl_complete": False,
    }

    # Step 1: pick a recipe if not already picked
    if not contract.selected_recipe_id:
        rid, conf = _resolve_recipe_pick(message, recipes)
        if rid is not None:
            result["selected_recipe_id"] = rid
            result["selected_recipe_confidence"] = conf
            title = next((r.get("title", rid) for r in recipes if r.get("id") == rid), rid)
            result["reply"] = (
                f"Great — I'll set up the pipeline for '{title}'. "
                f"That's everything I need to start; I'll begin configuring now."
            )
            # v1 fallback marks complete on recipe pick alone. The Workflow
            # Planner (Task 12) can prompt for follow-up preferences later.
            result["hitl_complete"] = True
        else:
            result["reply"] = _format_recipe_menu(recipes)
        return result

    # If we already have a recipe, keyword fallback treats any input as an
    # implicit "no additional preferences" and completes. The LLM path handles
    # richer follow-ups; the fallback stays deliberately minimal to avoid
    # re-introducing per-domain heuristics.
    result["hitl_complete"] = True
    result["reply"] = "Preferences noted. I'll configure the pipeline now."
    return result


# ─── Public API ───────────────────────────────────────────────────────────────

def extract_hitl_turn(
    message: str,
    history: list[dict],
    contract: HITLContract,
    dic_context: dict | None = None,
) -> HITLTurnExtraction:
    """Extract HITL fields from one user turn.

    Tries Qwen 32B via OpenRouter first (with a dataset-aware system prompt
    built from dic_context); falls back to recipe-aware keyword heuristics.
    Returns a HITLTurnExtraction with only the fields that changed this turn.
    """
    dic_context = dic_context or {}
    api_key = _get_api_key()

    if api_key:
        try:
            raw = _call_llm(message, history, contract, dic_context, api_key)
            parsed = _parse_llm_json(raw)
            if parsed:
                # Only accept fields we actually know about — silently drop
                # any legacy ETP keys that a cached prompt might return.
                accepted = {
                    k: parsed.get(k, v)
                    for k, v in HITLTurnExtraction().model_dump().items()
                }
                return HITLTurnExtraction(**accepted)
        except Exception as exc:
            logger.warning(f"[HITLExtraction] LLM call failed, using fallback: {exc}")

    parsed = _fallback_extract(message, contract, dic_context)
    accepted = {
        k: parsed.get(k, v)
        for k, v in HITLTurnExtraction().model_dump().items()
    }
    return HITLTurnExtraction(**accepted)
