"""
hitl_extraction.py — LLM extraction layer for the HITL phase.

Mirrors pre_upload_extraction.py:
  - Builds a domain-aware system prompt loaded from the HTDS spec context.
  - Calls Qwen 32B (OpenRouter) to extract structured HITLTurnExtraction JSON.
  - Falls back to keyword heuristics if the API is unavailable.

The LLM is the intelligence — questions, phrasing, and branching
all live in the system prompt, NOT in hardcoded strings.
"""

from __future__ import annotations

import json
import logging
import os
import re

from hitl_schemas import HITLContract, HITLTurnExtraction

logger = logging.getLogger(__name__)


# ─── System prompt (HTDS domain context + question blueprint) ─────────────────

_HITL_SYSTEM_PROMPT = """\
You are a conversational assistant for AIConnex, an autonomous AI platform
serving industrial effluent treatment plant (ETP) managers and process engineers.
You are NOT a data scientist — you speak plain English, like a trusted colleague
on the plant floor.

═══════════════════════════════════════════════════════
DATASET CONTEXT (already compiled — do not ask about it)
═══════════════════════════════════════════════════════
Name:        HTDS Industrial Effluent Dataset (HTDS-v1.csv)
Source:      Laurus Labs Ltd (Unit-3) pharmaceutical facility
Description: Daily wastewater batch deliveries to the Effluent Treatment Plant
Records:     883 daily batch readings (Jan 2024 → May 2025)

Parameters (plain English):
  • TDS  — Total Dissolved Solids (salt & mineral concentration, mg/L)
           Used for evaporator and RO plant planning.
  • COD  — Chemical Oxygen Demand (organic solvent load, mg/L)
           Indicates risk of killing biological ETP bacteria.
  • PH   — Acidity/Alkalinity level. Acid rinses = low pH, caustic rinses = high pH.
  • VOL  — Volume of wastewater received (cubic metres per day).
  • AN   — Ammoniacal Nitrogen (nitrogenous compound byproducts).
  • SS   — Suspended Solids (undissolved particulate matter).

Legal compliance ceiling: TDS < 50,000 mg/L, COD < 110,000 mg/L

═══════════════════════════════════════════════════════
YOUR TASK: HITL CLARIFICATION PHASE
═══════════════════════════════════════════════════════
The dataset is compiled. You must now gather 3–4 operational preferences
from the plant manager before the AI training pipeline can start.

Ask ONE question at a time, in this order. Wait for the answer before
moving to the next question.

QUESTION 1 — Operational Goal (ALWAYS ask first):
  "What is the main task you would like AIConnex to perform for your plant?"
  Present these options clearly:
    A — Predict tomorrow's TDS salinity level
        (so the evaporator and RO plant team can plan ahead)
    B — Alert me immediately when a chemical shock or organic solvent spill occurs
        (real-time contamination monitoring)
    C — Run a silent background monitor, but automatically activate a TDS forecast
        the moment a chemical shock is detected
        (smart combined system — recommended for most ETP plants)

QUESTION 2 — Chemical Parameter Focus (ALWAYS ask after Q1):
  "Which chemical parameter is your highest priority to track?"
    A — Total Dissolved Solids (TDS) — salt concentration and evaporator load
    B — Chemical Oxygen Demand (COD) — organic solvent load and biological treatment safety
    C — Both TDS and COD together

QUESTION 3 — Alert Sensitivity (ONLY ask if user chose B or C in Question 1):
  "How sensitive should the chemical shock alarm be?"
    A — High sensitivity: warn me early, even for mild pH drops or slight COD increases
    B — Balanced: flag confirmed chemical shocks only (recommended for most plants)
    C — Critical alerts only: notify me only when legal discharge limits are close to breach

QUESTION 4 — Dashboard Format (ONLY ask if user chose A in Question 1):
  "How should tomorrow's forecast be shown on your control room display?"
    A — Show the exact predicted number (e.g. "Tomorrow's TDS: 39,960 mg/L")
    B — Show a traffic light status (GREEN = normal, YELLOW = watchlist, RED = emergency)
    C — Show both the exact number and the traffic light status

═══════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════
1. NEVER use technical jargon: no "target column", "DAG", "regression",
   "algorithm", "hyperparameter", "feature engineering", or "model training".
2. Ask exactly ONE question per turn. Never dump all questions at once.
3. Acknowledge the user's previous answer warmly before asking the next question.
4. If the user says something unclear, gently ask them to choose from the options.
5. When all required questions are answered, write a warm confirmation summary
   and set hitl_complete = true.

═══════════════════════════════════════════════════════
OUTPUT FORMAT (STRICT — JSON only, no other text)
═══════════════════════════════════════════════════════
Return a JSON object with these fields:
{
  "operational_goal": "<regression_forecast|anomaly_alert|hybrid_smart_activate|null>",
  "operational_goal_confidence": <0.0-1.0>,
  "primary_parameter": "<TDS|COD|both|null>",
  "primary_parameter_confidence": <0.0-1.0>,
  "alert_sensitivity": "<high|balanced|critical_only|null>",
  "alert_sensitivity_confidence": <0.0-1.0>,
  "display_format": "<exact_number|traffic_light|both|null>",
  "display_format_confidence": <0.0-1.0>,
  "reply": "<your warm, plain-English conversational reply to show the user>",
  "hitl_complete": <true|false>
}

Only populate fields that were determined THIS turn. Set others to null / 0.0.
The "reply" field is what the terminal will print to the user.
"""


# ─── API key helper (identical to pre_upload_extraction.py) ──────────────────

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


# ─── LLM call ─────────────────────────────────────────────────────────────────

def _call_llm(
    message: str,
    history: list[dict],
    contract: HITLContract,
    api_key: str,
) -> str:
    """Call Qwen 32B via OpenRouter. Returns raw JSON string."""
    from openai import OpenAI

    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model    = os.environ.get("LLM_MODEL", "qwen/qwen-2.5-coder-32b-instruct")

    # Inject current contract state so LLM knows what's already answered
    contract_summary = (
        f"\nCURRENT HITL STATE (already answered — do not re-ask these):\n"
        f"  Q1 operational_goal:  {contract.operational_goal or 'NOT YET ANSWERED'}\n"
        f"  Q2 primary_parameter: {contract.primary_parameter or 'NOT YET ANSWERED'}\n"
        f"  Q3 alert_sensitivity: {contract.alert_sensitivity or 'NOT YET ANSWERED / NOT REQUIRED'}\n"
        f"  Q4 display_format:    {contract.display_format or 'NOT YET ANSWERED / NOT REQUIRED'}\n"
    )

    messages = [{"role": "system", "content": _HITL_SYSTEM_PROMPT + contract_summary}]

    for turn in history or []:
        role = "user" if turn.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": turn.get("content", "")})

    messages.append({"role": "user", "content": message})

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=12.0)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()


# ─── JSON parse helper ────────────────────────────────────────────────────────

def _parse_llm_json(raw: str) -> dict:
    """Extract JSON from LLM output (handles markdown code fences)."""
    raw = raw.strip()
    # Strip ```json ... ``` fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if match:
        raw = match.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting the first {...} block
        brace_match = re.search(r"\{[\s\S]+\}", raw)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except Exception:
                pass
    logger.warning(f"[HITLExtraction] Could not parse LLM JSON:\n{raw}")
    return {}


# ─── Keyword fallback ─────────────────────────────────────────────────────────

def _fallback_extract(message: str, contract: HITLContract) -> dict:
    """Rule-based fallback when LLM API is unavailable."""
    text = message.lower().strip()

    result: dict = {
        "operational_goal": None, "operational_goal_confidence": 0.0,
        "primary_parameter": None, "primary_parameter_confidence": 0.0,
        "alert_sensitivity": None, "alert_sensitivity_confidence": 0.0,
        "display_format": None, "display_format_confidence": 0.0,
        "reply": "", "hitl_complete": False,
    }

    # ── Q1 ──
    if not contract.operational_goal:
        if any(k in text for k in ("predict", "forecast", "tomorrow", "salinity", "1", "a")):
            result["operational_goal"] = "regression_forecast"
            result["operational_goal_confidence"] = 0.85
            result["reply"] = (
                "Got it — you'd like to forecast tomorrow's TDS salinity level.\n\n"
                "Now, which chemical parameter is your highest priority to track?\n\n"
                "  A — Total Dissolved Solids (TDS) — salt concentration\n"
                "  B — Chemical Oxygen Demand (COD) — organic load\n"
                "  C — Both TDS and COD together"
            )
        elif any(k in text for k in ("alert", "alarm", "spill", "shock", "detect", "2", "b")):
            result["operational_goal"] = "anomaly_alert"
            result["operational_goal_confidence"] = 0.85
            result["reply"] = (
                "Understood — you want real-time alerts for chemical shocks or spills.\n\n"
                "Which chemical parameter is your highest priority?\n\n"
                "  A — Total Dissolved Solids (TDS)\n"
                "  B — Chemical Oxygen Demand (COD)\n"
                "  C — Both TDS and COD"
            )
        elif any(k in text for k in ("hybrid", "smart", "combined", "monitor", "3", "c")):
            result["operational_goal"] = "hybrid_smart_activate"
            result["operational_goal_confidence"] = 0.85
            result["reply"] = (
                "Smart choice — the combined monitor will run quietly and activate "
                "a forecast the moment a chemical shock is detected.\n\n"
                "Which chemical parameter is your highest priority?\n\n"
                "  A — TDS (salt concentration)\n"
                "  B — COD (organic load)\n"
                "  C — Both TDS and COD"
            )
        else:
            result["reply"] = (
                "What is the main task you'd like AIConnex to perform for your plant?\n\n"
                "  A — Predict tomorrow's TDS salinity level\n"
                "  B — Alert me when a chemical shock or organic spill occurs\n"
                "  C — Run a silent monitor, activate a forecast when a shock is detected (recommended)"
            )
        return result

    # ── Q2 ──
    if not contract.primary_parameter:
        if any(k in text for k in ("tds", "salt", "dissolved", "1", "a")):
            result["primary_parameter"] = "TDS"
            result["primary_parameter_confidence"] = 0.9
        elif any(k in text for k in ("cod", "organic", "solvent", "2", "b")):
            result["primary_parameter"] = "COD"
            result["primary_parameter_confidence"] = 0.9
        elif any(k in text for k in ("both", "all", "together", "3", "c")):
            result["primary_parameter"] = "both"
            result["primary_parameter_confidence"] = 0.9
        if result["primary_parameter"]:
            # Route to Q3 or Q4
            if contract.operational_goal == "regression_forecast":
                result["reply"] = (
                    "Perfect. How should tomorrow's forecast be shown on your control room display?\n\n"
                    "  A — Exact predicted number (e.g. \"Tomorrow's TDS: 39,960 mg/L\")\n"
                    "  B — Traffic light status (GREEN / YELLOW / RED)\n"
                    "  C — Both number and traffic light"
                )
            else:
                result["reply"] = (
                    "Noted. How sensitive should the chemical shock alarm be?\n\n"
                    "  A — High sensitivity: early warning on subtle changes\n"
                    "  B — Balanced: flag confirmed shocks (recommended)\n"
                    "  C — Critical only: legal limit breaches only"
                )
        else:
            result["reply"] = (
                "Which chemical parameter is your highest priority?\n\n"
                "  A — Total Dissolved Solids (TDS)\n"
                "  B — Chemical Oxygen Demand (COD)\n"
                "  C — Both TDS and COD together"
            )
        return result

    # ── Q3 (anomaly / hybrid) ──
    if contract.operational_goal in ("anomaly_alert", "hybrid_smart_activate") and not contract.alert_sensitivity:
        if any(k in text for k in ("high", "early", "sensitive", "1", "a")):
            result["alert_sensitivity"] = "high"
            result["alert_sensitivity_confidence"] = 0.9
        elif any(k in text for k in ("balanced", "confirmed", "recommend", "2", "b")):
            result["alert_sensitivity"] = "balanced"
            result["alert_sensitivity_confidence"] = 0.9
        elif any(k in text for k in ("critical", "legal", "limit", "severe", "3", "c")):
            result["alert_sensitivity"] = "critical_only"
            result["alert_sensitivity_confidence"] = 0.9
        if result["alert_sensitivity"]:
            result["hitl_complete"] = True
            result["reply"] = (
                "All set. I have everything I need to configure your monitoring system.\n\n"
                "I'll set up the pipeline now — this will only take a moment."
            )
        else:
            result["reply"] = (
                "How sensitive should the chemical shock alarm be?\n\n"
                "  A — High sensitivity: warn early on subtle pH drops or mild COD surges\n"
                "  B — Balanced: flag confirmed shocks (recommended)\n"
                "  C — Critical only: legal discharge limit breaches"
            )
        return result

    # ── Q4 (forecast) ──
    if contract.operational_goal == "regression_forecast" and not contract.display_format:
        if any(k in text for k in ("exact", "number", "mg", "1", "a")):
            result["display_format"] = "exact_number"
            result["display_format_confidence"] = 0.9
        elif any(k in text for k in ("traffic", "light", "colour", "color", "green", "2", "b")):
            result["display_format"] = "traffic_light"
            result["display_format_confidence"] = 0.9
        elif any(k in text for k in ("both", "all", "together", "3", "c")):
            result["display_format"] = "both"
            result["display_format_confidence"] = 0.9
        if result["display_format"]:
            result["hitl_complete"] = True
            result["reply"] = (
                "All set! I have everything I need to start the forecasting pipeline.\n\n"
                "I'll begin configuring the AI model now — this will take just a moment."
            )
        else:
            result["reply"] = (
                "How should tomorrow's forecast be displayed?\n\n"
                "  A — Exact number in mg/L\n"
                "  B — Traffic light status (GREEN / YELLOW / RED)\n"
                "  C — Both number and traffic light"
            )
        return result

    result["hitl_complete"] = True
    result["reply"] = "All preferences captured. Ready to configure the pipeline."
    return result


# ─── Public API ───────────────────────────────────────────────────────────────

def extract_hitl_turn(
    message: str,
    history: list[dict],
    contract: HITLContract,
) -> HITLTurnExtraction:
    """
    Extract HITL fields from one user turn.

    Tries Qwen 32B via OpenRouter first; falls back to keyword heuristics.
    Returns a HITLTurnExtraction with only the fields that changed this turn.
    """
    api_key = _get_api_key()

    if api_key:
        try:
            raw = _call_llm(message, history, contract, api_key)
            parsed = _parse_llm_json(raw)
            if parsed:
                return HITLTurnExtraction(**{
                    k: parsed.get(k, v)
                    for k, v in HITLTurnExtraction().model_dump().items()
                })
        except Exception as exc:
            logger.warning(f"[HITLExtraction] LLM call failed, using fallback: {exc}")

    # Fallback
    parsed = _fallback_extract(message, contract)
    return HITLTurnExtraction(**{
        k: parsed.get(k, v)
        for k, v in HITLTurnExtraction().model_dump().items()
    })
