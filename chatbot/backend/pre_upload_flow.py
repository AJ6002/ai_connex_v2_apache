"""
Per-turn algorithm for the pre-upload intent-gathering flow.

Implements the 6-step process:
  1. Extraction — call LLM for new/updated fields
  2. Merge — update contract only where confidence is higher
  3. Gap analysis — compare against REQUIRED/RECOMMENDED lists
  4. Question selection — pick the single highest-priority question
  5. Escalation — detect ambiguity loops, offer quick-select
  6. Completion check — flip conversation_complete when all REQUIRED filled
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from pre_upload_schemas import (
    PreUploadContract,
    TurnExtraction,
    CandidateMLProblemType,
    ClarificationItem,
    ConversationMeta,
    Goal,
    Observed,
    Inferred,
    InferredField,
    DatasetExpectation,
    Constraints,
    ConversationAnalysis,
    Urgency,
    PlanningHints,
    Metadata,
)
from pre_upload_config import (
    REQUIRED_FIELDS,
    RECOMMENDED_FIELDS,
    OPPORTUNISTIC_FIELDS,
    MIN_CONFIDENCE_TO_ACCEPT,
    REQUIRED_CONFIDENCE_THRESHOLD,
    RECOMMENDED_CONFIDENCE_THRESHOLD,
    MAX_AMBIGUOUS_TURNS,
    MAX_ASKED_SAME_FIELD,
    FieldTierEntry,
)
from pre_upload_extraction import extract_pre_upload_turn
from pre_upload_state import (
    load_contract,
    save_contract,
    load_replies,
    append_reply,
    create_new_session,
)

# ──────────────────────────────────────────────
# Question templates (one per field)
# ──────────────────────────────────────────────

_QUESTION_TEMPLATES: dict[str, str] = {
    "goal.primary_goal": "Could you tell me what you're hoping to achieve? What's the main goal or problem you'd like to solve?",
    "goal.candidate_ml_problem_types": "What kind of machine learning problem are you looking at — for example, regression, classification, forecasting, or anomaly detection?",
    "dataset_expectation.expected_dataset_type": "What type of data will you be working with? For example, time-series sensor data, tabular data, images, or text?",
    "dataset_expectation.expected_file_types": "What file format will your data be in — CSV, JSON, Parquet, or something else?",
    "inferred.industry": "Which industry or sector are you operating in?",
    "inferred.user_role": "What's your role — are you a data scientist, engineer, analyst, or something else?",
    "constraints.explainability_required": "Do you need the model to be explainable or interpretable, or is a black-box approach acceptable?",
}


def _get_question_for_field(path: str) -> str:
    """Get a natural-language question for a field path."""
    return _QUESTION_TEMPLATES.get(path, f"Could you tell me more about {path.replace('_', ' ')}?")


# ──────────────────────────────────────────────
# Merge logic
# ──────────────────────────────────────────────


def _set_nested(contract: PreUploadContract, path: str, value):
    """Set a value on the contract using a dot-separated path."""
    parts = path.split(".")
    obj = contract
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)


def _get_nested(contract: PreUploadContract, path: str):
    """Get a value from the contract using a dot-separated path."""
    parts = path.split(".")
    obj = contract
    for part in parts:
        obj = getattr(obj, part)
    return obj


def _merge_extraction(contract: PreUploadContract, extraction: TurnExtraction) -> PreUploadContract:
    """Merge a TurnExtraction into the contract, only accepting values
    with confidence >= MIN_CONFIDENCE_TO_ACCEPT and strictly higher than
    what's already stored."""

    # ── Goal fields ──
    if extraction.primary_goal is not None and extraction.primary_goal_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        # Only overwrite if field is empty, or new confidence is high enough to be trustworthy
        if not contract.goal.primary_goal or extraction.primary_goal_confidence >= REQUIRED_CONFIDENCE_THRESHOLD:
            contract.goal.primary_goal = extraction.primary_goal

    if extraction.secondary_goals is not None and extraction.secondary_goals_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        # Merge lists (don't replace, add unique items)
        existing = set(contract.goal.secondary_goals)
        for g in extraction.secondary_goals:
            if g not in existing:
                contract.goal.secondary_goals.append(g)

    if extraction.business_problem is not None and extraction.business_problem_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if not contract.goal.business_problem or extraction.business_problem_confidence >= REQUIRED_CONFIDENCE_THRESHOLD:
            contract.goal.business_problem = extraction.business_problem

    if extraction.candidate_ml_problem_types is not None and extraction.candidate_ml_problem_types_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        # Merge ML problem types: add new ones, update confidence for existing
        existing_types = {p.type: p for p in contract.goal.candidate_ml_problem_types}
        for new_type in extraction.candidate_ml_problem_types:
            if new_type.type in existing_types:
                if new_type.confidence > existing_types[new_type.type].confidence:
                    existing_types[new_type.type].confidence = new_type.confidence
            else:
                contract.goal.candidate_ml_problem_types.append(new_type)

    # ── Observed fields (always append, no confidence needed) ──
    if extraction.industry_terms:
        existing = set(contract.observed.industry_terms)
        for item in extraction.industry_terms:
            if item not in existing:
                contract.observed.industry_terms.append(item)
                existing.add(item)

    if extraction.equipment:
        existing = set(contract.observed.equipment)
        for item in extraction.equipment:
            if item not in existing:
                contract.observed.equipment.append(item)
                existing.add(item)

    if extraction.assets:
        existing = set(contract.observed.assets)
        for item in extraction.assets:
            if item not in existing:
                contract.observed.assets.append(item)
                existing.add(item)

    if extraction.datasets_mentioned:
        existing = set(contract.observed.datasets_mentioned)
        for item in extraction.datasets_mentioned:
            if item not in existing:
                contract.observed.datasets_mentioned.append(item)
                existing.add(item)

    if extraction.locations:
        existing = set(contract.observed.locations)
        for item in extraction.locations:
            if item not in existing:
                contract.observed.locations.append(item)
                existing.add(item)

    if extraction.time_periods:
        existing = set(contract.observed.time_periods)
        for item in extraction.time_periods:
            if item not in existing:
                contract.observed.time_periods.append(item)
                existing.add(item)

    if extraction.quantities:
        existing = set(contract.observed.quantities)
        for item in extraction.quantities:
            if item not in existing:
                contract.observed.quantities.append(item)
                existing.add(item)

    if extraction.keywords:
        existing = set(contract.observed.keywords)
        for item in extraction.keywords:
            if item not in existing:
                contract.observed.keywords.append(item)
                existing.add(item)

    if extraction.user_statements:
        existing = set(contract.observed.user_statements)
        for item in extraction.user_statements:
            if item not in existing:
                contract.observed.user_statements.append(item)
                existing.add(item)

    # ── Inferred fields (confidence-gated) ──
    if extraction.industry is not None and extraction.industry_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if extraction.industry_confidence > contract.inferred.industry.confidence:
            contract.inferred.industry.value = extraction.industry
            contract.inferred.industry.confidence = extraction.industry_confidence

    if extraction.user_role is not None and extraction.user_role_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if extraction.user_role_confidence > contract.inferred.user_role.confidence:
            contract.inferred.user_role.value = extraction.user_role
            contract.inferred.user_role.confidence = extraction.user_role_confidence

    if extraction.business_domain is not None and extraction.business_domain_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if extraction.business_domain_confidence > contract.inferred.business_domain.confidence:
            contract.inferred.business_domain.value = extraction.business_domain
            contract.inferred.business_domain.confidence = extraction.business_domain_confidence

    if extraction.experience_level is not None and extraction.experience_level_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if extraction.experience_level_confidence > contract.inferred.experience_level.confidence:
            contract.inferred.experience_level.value = extraction.experience_level
            contract.inferred.experience_level.confidence = extraction.experience_level_confidence

    # ── Dataset expectation fields ──
    if extraction.expected_file_types is not None and extraction.expected_file_types_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        existing = set(contract.dataset_expectation.expected_file_types)
        for ft in extraction.expected_file_types:
            if ft not in existing:
                contract.dataset_expectation.expected_file_types.append(ft)
                existing.add(ft)

    if extraction.expected_dataset_type is not None and extraction.expected_dataset_type_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if not contract.dataset_expectation.expected_dataset_type or extraction.expected_dataset_type_confidence >= REQUIRED_CONFIDENCE_THRESHOLD:
            contract.dataset_expectation.expected_dataset_type = extraction.expected_dataset_type

    if extraction.expected_duration is not None and extraction.expected_duration_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if not contract.dataset_expectation.expected_duration or extraction.expected_duration_confidence >= REQUIRED_CONFIDENCE_THRESHOLD:
            contract.dataset_expectation.expected_duration = extraction.expected_duration

    if extraction.expected_sampling_rate is not None and extraction.expected_sampling_rate_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if not contract.dataset_expectation.expected_sampling_rate or extraction.expected_sampling_rate_confidence >= REQUIRED_CONFIDENCE_THRESHOLD:
            contract.dataset_expectation.expected_sampling_rate = extraction.expected_sampling_rate

    if extraction.expected_size is not None and extraction.expected_size_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if not contract.dataset_expectation.expected_size or extraction.expected_size_confidence >= REQUIRED_CONFIDENCE_THRESHOLD:
            contract.dataset_expectation.expected_size = extraction.expected_size

    # ── Constraints ──
    if extraction.preferred_algorithms is not None:
        existing = set(contract.constraints.preferred_algorithms)
        for a in extraction.preferred_algorithms:
            if a not in existing:
                contract.constraints.preferred_algorithms.append(a)
                existing.add(a)

    if extraction.preferred_frameworks is not None:
        existing = set(contract.constraints.preferred_frameworks)
        for fw in extraction.preferred_frameworks:
            if fw not in existing:
                contract.constraints.preferred_frameworks.append(fw)
                existing.add(fw)

    if extraction.explainability_required is not None and extraction.explainability_required_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        contract.constraints.explainability_required = extraction.explainability_required

    if extraction.deployment_constraints is not None:
        existing = set(contract.constraints.deployment_constraints)
        for dc in extraction.deployment_constraints:
            if dc not in existing:
                contract.constraints.deployment_constraints.append(dc)
                existing.add(dc)

    if extraction.business_constraints is not None:
        existing = set(contract.constraints.business_constraints)
        for bc in extraction.business_constraints:
            if bc not in existing:
                contract.constraints.business_constraints.append(bc)
                existing.add(bc)

    if extraction.technical_constraints is not None:
        existing = set(contract.constraints.technical_constraints)
        for tc in extraction.technical_constraints:
            if tc not in existing:
                contract.constraints.technical_constraints.append(tc)
                existing.add(tc)

    # ── Conversation analysis ──
    if extraction.urgency is not None and extraction.urgency_confidence >= MIN_CONFIDENCE_TO_ACCEPT:
        if extraction.urgency_confidence > contract.conversation_analysis.urgency.confidence:
            contract.conversation_analysis.urgency.value = extraction.urgency
            contract.conversation_analysis.urgency.confidence = extraction.urgency_confidence

    if extraction.sentiment is not None:
        contract.conversation_analysis.sentiment = extraction.sentiment

    if extraction.certainty_level is not None:
        contract.conversation_analysis.certainty_level = extraction.certainty_level

    if extraction.ambiguity_detected is not None:
        contract.conversation_analysis.ambiguity_detected = extraction.ambiguity_detected

    # ── Planning ──
    if extraction.recommended_next_action is not None:
        contract.planning_hints.recommended_next_action = extraction.recommended_next_action

    if extraction.wait_for_dataset is not None:
        contract.planning_hints.wait_for_dataset = extraction.wait_for_dataset

    return contract


# ──────────────────────────────────────────────
# Gap analysis
# ──────────────────────────────────────────────


def _is_field_filled(contract: PreUploadContract, entry: FieldTierEntry) -> bool:
    """Check if a field is filled above its tier's confidence threshold."""
    value = _get_nested(contract, entry.path)

    # Determine threshold based on tier
    if entry in REQUIRED_FIELDS:
        threshold = REQUIRED_CONFIDENCE_THRESHOLD
    elif entry in RECOMMENDED_FIELDS:
        threshold = RECOMMENDED_CONFIDENCE_THRESHOLD
    else:
        threshold = MIN_CONFIDENCE_TO_ACCEPT

    # Check if the field has a value
    if isinstance(value, str):
        return bool(value)
    elif isinstance(value, list):
        return len(value) > 0
    elif isinstance(value, bool):
        return True  # booleans are always "filled" if set
    elif value is None:
        return False  # Optional fields that are None are not filled
    elif isinstance(value, InferredField):
        return bool(value.value) and value.confidence >= threshold
    elif isinstance(value, list) and value and hasattr(value[0], "type"):
        return len(value) > 0 and max(c.confidence for c in value) >= threshold
    return False


def _run_gap_analysis(contract: PreUploadContract) -> list[ClarificationItem]:
    """Compare the merged contract against REQUIRED and RECOMMENDED lists.
    Returns a list of ClarificationItems sorted by priority."""
    items: list[ClarificationItem] = []

    # Check REQUIRED fields first
    for entry in REQUIRED_FIELDS:
        if not _is_field_filled(contract, entry):
            items.append(ClarificationItem(
                question=_get_question_for_field(entry.path),
                reason=f"Required field '{entry.label or entry.path}' is still missing",
                priority="high",
            ))

    # Check RECOMMENDED fields
    for entry in RECOMMENDED_FIELDS:
        if not _is_field_filled(contract, entry):
            items.append(ClarificationItem(
                question=_get_question_for_field(entry.path),
                reason=f"Recommended field '{entry.label or entry.path}' is still missing",
                priority="medium",
            ))

    return items


# ──────────────────────────────────────────────
# Question selection
# ──────────────────────────────────────────────


def _select_question(
    clarifications: list[ClarificationItem],
    contract: PreUploadContract,
    replies: list[dict],
) -> Optional[str]:
    """Select the single highest-priority question to ask.
    Returns None if no clarifications are needed."""
    if not clarifications:
        return None

    # Sort by priority (high first), then by how many turns it's been missing
    priority_order = {"high": 0, "medium": 1, "low": 2}
    clarifications.sort(key=lambda c: priority_order.get(c.priority, 99))

    # Take the highest priority item
    return clarifications[0].question


# ──────────────────────────────────────────────
# Escalation detection
# ──────────────────────────────────────────────


def _check_escalation(
    contract: PreUploadContract,
    replies: list[dict],
    previous_contract: Optional[PreUploadContract],
) -> bool:
    """Check if we should offer quick-select menu instead of another open-ended question.
    Returns True if escalation is needed."""
    turn_num = getattr(contract.conversation, "conversation_turn", 1)

    # Check 1: Turn 2+ and primary_goal is still un-filled (user giving repeated low-info inputs like 'hi', 'hi again')
    if turn_num >= 2 and not contract.goal.primary_goal:
        return True

    # Check 2: ambiguity detected for 2+ consecutive turns
    if contract.conversation_analysis.ambiguity_detected:
        if previous_contract and previous_contract.conversation_analysis.ambiguity_detected:
            return True

    # Check 3: same field asked 2+ times without being filled
    if len(replies) >= 2:
        last_question = replies[-1].get("question", "") if replies else ""
        if last_question:
            count = sum(1 for r in replies if r.get("question") == last_question)
            if count >= MAX_ASKED_SAME_FIELD:
                return True

    return False


# ──────────────────────────────────────────────
# Completion check
# ──────────────────────────────────────────────


def _check_completion(contract: PreUploadContract) -> bool:
    """Check if all REQUIRED fields are filled above threshold."""
    for entry in REQUIRED_FIELDS:
        if not _is_field_filled(contract, entry):
            return False
    return True


# ──────────────────────────────────────────────
# Main per-turn handler
# ──────────────────────────────────────────────


def process_turn(
    message: str,
    session_id: str,
    conversation_id: str = "",
    history: Optional[list] = None,
) -> dict:
    """Process one turn of the pre-upload conversation.

    Args:
        message: The user's message
        session_id: The session ID (empty string for new sessions)
        conversation_id: Optional conversation ID
        history: Optional conversation history

    Returns:
        dict with keys: reply, session_id, conversation_complete, recommended_next_action
    """
    start_time = time.time()

    # Load or create session
    if not session_id:
        session_id, contract = create_new_session(conversation_id)
        previous_contract = None
    else:
        contract = load_contract(session_id)
        if contract is None:
            session_id, contract = create_new_session(conversation_id)
            previous_contract = None
        else:
            previous_contract = contract.model_copy(deep=True)
            contract.conversation.conversation_turn += 1

    # Load replies log
    replies = load_replies(session_id)

    # Step 1: Extraction
    extraction = extract_pre_upload_turn(message, history or [], contract)

    # Step 2: Merge
    contract = _merge_extraction(contract, extraction)

    # Step 3: Gap analysis
    clarifications = _run_gap_analysis(contract)
    contract.clarifications_required = clarifications
    contract.conversation_analysis.missing_information = [
        c.reason for c in clarifications
    ]

    # Step 4: Question selection
    question = _select_question(clarifications, contract, replies)

    # Step 5: Escalation check
    needs_escalation = _check_escalation(contract, replies, previous_contract)

    # Step 6: Completion check
    is_complete = _check_completion(contract)
    contract.planning_hints.conversation_complete = is_complete

    if is_complete:
        contract.planning_hints.recommended_next_action = "prompt_for_upload"
        contract.planning_hints.wait_for_dataset = True
        raw_prompt = "Great, I have all the information I need! You can now upload your dataset and I'll take it from here."
    elif needs_escalation:
        contract.planning_hints.recommended_next_action = "offer_quick_select"
        raw_prompt = (
            "I notice you might be unsure where to start. Here are the primary task pipelines I can build for you:\n"
            "1. Target Prediction / Regression (e.g. predicting TDS, COD, pH, or concentration levels)\n"
            "2. Time-Series Forecasting (e.g. 7-day effluent load trajectories)\n"
            "3. Anomaly & Outlier Detection (e.g. catching contamination spills)\n\n"
            "Which of these matches what you want to achieve with your data?"
        )
    elif question:
        contract.planning_hints.recommended_next_action = "ask_clarification"
        raw_prompt = question
    else:
        contract.planning_hints.recommended_next_action = "prompt_for_upload"
        raw_prompt = "Thanks! I have a good understanding of your needs. Feel free to upload your dataset whenever you're ready."

    # Generate 100% dynamic, conversational phrasing using OpenRouter Qwen 32B
    from llm_responder import generate_llm_response
    reply = generate_llm_response(
        message,
        intent=contract.goal.primary_goal or "pre_upload_intent",
        context_data={
            "status": "intake_gathering" if not is_complete else "pre_upload_ready",
            "guide_prompt": raw_prompt,
            "is_complete": is_complete,
            "needs_escalation": needs_escalation,
            "turn": contract.conversation.conversation_turn,
            "missing": contract.conversation_analysis.missing_information,
        }
    )


    # Update metadata
    contract.metadata.processing_time_ms = int((time.time() - start_time) * 1000)
    contract.metadata.llm_model = "qwen-2.5-coder-32b-instruct"

    # Save contract
    save_contract(session_id, contract)

    # Append to replies log
    append_reply(session_id, contract.conversation.conversation_turn, reply, message)


    return {
        "reply": reply,
        "session_id": session_id,
        "conversation_complete": is_complete,
        "recommended_next_action": contract.planning_hints.recommended_next_action,
        "ambiguity_detected": contract.conversation_analysis.ambiguity_detected,
        "missing_information": contract.conversation_analysis.missing_information,
    }