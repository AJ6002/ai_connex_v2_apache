"""
AI Connexx chatbot backend (Flask).

Route: POST /api/chat  -- accepts {message, history} exactly like the
existing Express route in server.ts, and returns {reply, topologyAssigned,
dagMatched, recipeCompiled} so the current MainChatView.tsx frontend needs
no changes.

Confidence-based routing (see the confidence-routing diagram discussed
earlier):
  - confidence >= HIGH_CONFIDENCE and risk != high_impact -> dispatch directly
  - confidence >= HIGH_CONFIDENCE and risk == high_impact -> ask for confirmation
  - MEDIUM <= confidence < HIGH                            -> ask a clarifying question
  - confidence < MEDIUM                                    -> fall back / "didn't understand"
"""

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

from intents import get_risk_tier, RiskTier
from extraction import extract_intent
from validation import validate
from dispatcher import dispatch, _badges_for
from pre_upload_flow import process_turn as pre_upload_process_turn

app = Flask(__name__)

HIGH_CONFIDENCE = 0.85
MEDIUM_CONFIDENCE = 0.5

# Simple in-memory pending-confirmation store, keyed by a client-provided
# conversation id. A real deployment would use a session/Redis store instead.
_PENDING_CONFIRMATIONS: dict[str, dict] = {}


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "operational", "servicesOnline": 9})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history", [])
    conversation_id = data.get("conversationId", "default")

    if not message:
        return jsonify({"reply": "I didn't receive a message.", **_badges_for(None)}), 400

    # Handle a pending high-impact confirmation first
    pending = _PENDING_CONFIRMATIONS.get(conversation_id)
    if pending:
        if message.strip().lower() in ("yes", "y", "confirm", "confirmed"):
            del _PENDING_CONFIRMATIONS[conversation_id]
            result = dispatch(pending["extracted"])
            return jsonify(result)
        elif message.strip().lower() in ("no", "n", "cancel"):
            del _PENDING_CONFIRMATIONS[conversation_id]
            return jsonify({"reply": "Cancelled.", **_badges_for(None)})
        # else: fall through and treat this message as a brand-new request

    # 1. Extraction (the NLP step)
    extracted = extract_intent(message, history)

    # 2. Confidence-based routing
    if extracted.confidence < MEDIUM_CONFIDENCE:
        return jsonify({
            "reply": "I wasn't able to understand that clearly. Could you rephrase, "
                     "e.g. mention the dataset name and what you'd like to do with it?",
            **_badges_for(None),
        })

    if extracted.confidence < HIGH_CONFIDENCE:
        return jsonify({
            "reply": f"Just to confirm -- did you mean to '{extracted.intent.replace('_', ' ')}'? "
                     "Please rephrase with the dataset name if so.",
            **_badges_for(extracted.entities.dataset_id),
        })

    # 3. Schema + state validation (the deterministic gate)
    outcome = validate(extracted)
    if not outcome.ok:
        if outcome.missing_entities:
            reply = f"I need a bit more info -- please specify: {', '.join(outcome.missing_entities)}."
        else:
            reply = " ".join(outcome.errors) or "That request couldn't be validated."
        return jsonify({"reply": reply, **_badges_for(extracted.entities.dataset_id)})

    # 4. High-impact intents require explicit confirmation before dispatch
    if outcome.needs_confirmation:
        _PENDING_CONFIRMATIONS[conversation_id] = {"extracted": extracted}
        return jsonify({
            "reply": f"This will {extracted.intent.replace('_', ' ')} for "
                     f"'{extracted.entities.dataset_id}'. Reply 'yes' to confirm or 'no' to cancel.",
            **_badges_for(extracted.entities.dataset_id),
        })

    # 5. Dispatch
    result = dispatch(extracted)
    return jsonify(result)


@app.route("/api/pre_upload/chat", methods=["POST"])
def pre_upload_chat():
    """Pre-upload intent-gathering conversation endpoint.

    Accepts:  {message, session_id, conversation_id}
    Returns:  {reply, session_id, conversation_complete,
               recommended_next_action, ambiguity_detected, missing_information}
    """
    data = request.get_json(force=True) or {}
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id", "")
    conversation_id = data.get("conversation_id", "")

    if not message:
        return jsonify({"reply": "I didn't receive a message.", "session_id": session_id}), 400

    result = pre_upload_process_turn(
        message=message,
        session_id=session_id,
        conversation_id=conversation_id,
    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
