"""
hitl_flow.py — Per-turn HITL conversation handler.

Mirrors pre_upload_flow.process_turn() exactly:
  1. Extract    — call LLM (or fallback) for this turn's new fields
  2. Merge      — update HITLContract only where confidence is higher
  3. Complete?  — check if all required fields for the chosen path are filled
  4. DAG Resolve— derive dag_pool, branch_ids, target_column from Q1+Q2

Returns a dict compatible with the terminal_runner loop.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from hitl_schemas import HITLContract, HITLTurnExtraction, resolve_dag_pool, _is_complete
from hitl_extraction import extract_hitl_turn

logger = logging.getLogger(__name__)

# Confidence threshold — only accept LLM-extracted fields above this
MIN_CONFIDENCE = 0.50


# ─── Merge ────────────────────────────────────────────────────────────────────

def _merge(contract: HITLContract, extraction: HITLTurnExtraction) -> HITLContract:
    """
    Merge extraction into contract — only accept a field if the new
    confidence is higher than what we already have (same pattern as pre_upload_flow).
    """
    field_conf_pairs = [
        ("operational_goal",  "operational_goal_confidence"),
        ("primary_parameter", "primary_parameter_confidence"),
        ("alert_sensitivity", "alert_sensitivity_confidence"),
        ("display_format",    "display_format_confidence"),
    ]
    for field, conf_field in field_conf_pairs:
        new_val  = getattr(extraction, field)
        new_conf = getattr(extraction, conf_field, 0.0)
        old_conf = getattr(contract, conf_field, 0.0)

        if new_val is not None and new_conf >= MIN_CONFIDENCE and new_conf >= old_conf:
            setattr(contract, field, new_val)
            setattr(contract, conf_field, new_conf)

    return contract


# ─── Opening prompt (HITL_START sentinel) ────────────────────────────────────

_FALLBACK_OPENING_MESSAGE = (
    "Great news — your dataset has been compiled and I have a clear picture "
    "of your effluent data. Before I start configuring the AI system, I have "
    "a few short questions to make sure we build exactly what your plant needs.\n\n"
    "What is the main task you would like AIConnex to perform?\n\n"
    "  A — Predict tomorrow's TDS salinity level\n"
    "      (so the evaporator and RO plant team can plan ahead)\n\n"
    "  B — Alert me immediately when a chemical shock or organic solvent spill occurs\n"
    "      (real-time contamination monitoring)\n\n"
    "  C — Run a silent background monitor, but automatically activate a TDS forecast\n"
    "      the moment a chemical shock is detected\n"
    "      (smart combined system — recommended for most ETP plants)"
)


def _build_recipe_opening(dic_context: dict) -> str:
    """Build a dynamic HITL opening prompt from DIC recipes catalog.

    Falls back to a static message if no recipes are present in the DIC.
    """
    recipes = dic_context.get("recipes", [])
    if not recipes:
        return _FALLBACK_OPENING_MESSAGE

    dataset_name = dic_context.get("dataset_identity", {}).get("name", "your dataset")

    lines = [
        f"Great news — your dataset '{dataset_name}' has been compiled and analysed.",
        "Based on the data I found, here are the available analytical objectives:\n",
    ]

    for i, r in enumerate(recipes, start=1):
        conf_pct = int(r.get("confidence", 1.0) * 100)
        task_tag = r.get("task", "")
        title = r.get("title", f"Recipe {i}")
        rationale = r.get("rationale", "")
        lines.append(f"  [{i}] {title}  [{task_tag} · {conf_pct}% confidence]")
        if rationale:
            lines.append(f"       {rationale}")

    lines.append("")
    lines.append("Please type the number of the objective you would like to pursue (e.g. 1, 2, 3).")

    return "\n".join(lines)


# ─── Public API ───────────────────────────────────────────────────────────────

def process_hitl_turn(
    message: str,
    session_id: str,
    dic_context: dict,
    contract=None,
    history=None,
) -> dict:
    """
    Process one HITL conversation turn.

    Args:
        message:     User's input (or "[HITL_START]" to open the conversation)
        session_id:  Current session ID (for MLflow logging)
        dic_context: Compiled DIC from Scout (passed to extraction for context)
        contract:    Current HITLContract (None = first turn)
        history:     Conversation history for multi-turn context

    Returns dict with:
        reply:            str  — LLM-generated message to display to user
        hitl_complete:    bool — True when all required fields collected
        contract:         HITLContract — updated state
        resolved_dag_pool: list[str]
        target_column:    str | None
        branch_ids:       list[str]
    """
    start = time.time()

    if contract is None:
        contract = HITLContract()

    contract.turn_count += 1

    # ── Opening turn: build dynamic prompt from DIC recipes ──────────────────
    if message.strip() == "[HITL_START]":
        opening = _build_recipe_opening(dic_context)
        return {
            "reply": opening,
            "hitl_complete": False,
            "contract": contract,
            "resolved_dag_pool": [],
            "target_column": None,
            "branch_ids": [],
        }



    # ── Step 1: Extract ───────────────────────────────────────────────────────
    extraction: HITLTurnExtraction = extract_hitl_turn(
        message=message,
        history=history or [],
        contract=contract,
    )

    # ── Step 2: Merge ─────────────────────────────────────────────────────────
    contract = _merge(contract, extraction)

    # ── Step 3: Completion check ──────────────────────────────────────────────
    complete = extraction.hitl_complete or _is_complete(contract)
    contract.hitl_complete = complete

    # ── Step 4: DAG resolution (once complete) ────────────────────────────────
    if complete:
        contract = resolve_dag_pool(contract)

    # ── Reply ─────────────────────────────────────────────────────────────────
    reply = extraction.reply or (
        "I've captured that. Let me know if you'd like to adjust anything."
        if complete else
        "Could you clarify? Please choose one of the options above."
    )

    elapsed_ms = int((time.time() - start) * 1000)
    logger.debug(
        f"[HITLFlow] turn={contract.turn_count} "
        f"goal={contract.operational_goal} param={contract.primary_parameter} "
        f"complete={complete} elapsed={elapsed_ms}ms"
    )

    return {
        "reply": reply,
        "hitl_complete": complete,
        "contract": contract,
        "resolved_dag_pool": contract.resolved_dag_pool,
        "target_column": contract.target_column,
        "branch_ids": contract.branch_ids,
        "elapsed_ms": elapsed_ms,
    }
