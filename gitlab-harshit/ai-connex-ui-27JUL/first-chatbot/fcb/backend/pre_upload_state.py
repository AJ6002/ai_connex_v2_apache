"""
Session state management for the pre-upload conversation phase.

Follows the swappable-store pattern from pipeline_state.py: starts with
a file-based store (JSON files in backend/data/sessions/) structured so
it can later be swapped for a real DB.

Stores two files per session:
  - user_intent_<session_id>.json       (the current contract, overwritten each turn)
  - user_intent_replies_<session_id>.json (append-only Q&A log)
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from pre_upload_schemas import PreUploadContract, ConversationMeta

# Directory where session files are stored
SESSION_DIR = os.path.join(os.path.dirname(__file__), "data", "sessions")


def _ensure_session_dir() -> None:
    os.makedirs(SESSION_DIR, exist_ok=True)


def _session_path(session_id: str) -> str:
    return os.path.join(SESSION_DIR, f"user_intent_{session_id}.json")


def _replies_path(session_id: str) -> str:
    return os.path.join(SESSION_DIR, f"user_intent_replies_{session_id}.json")


def generate_session_id() -> str:
    """Generate a new unique session ID."""
    return str(uuid.uuid4())


def load_contract(session_id: str) -> Optional[PreUploadContract]:
    """Load the current contract for a session, or None if it doesn't exist."""
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PreUploadContract.model_validate(data)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def save_contract(session_id: str, contract: PreUploadContract) -> None:
    """Overwrite the current contract for a session."""
    _ensure_session_dir()
    path = _session_path(session_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(contract.model_dump_json(indent=2))


def load_replies(session_id: str) -> list[dict]:
    """Load the Q&A log for a session, or return an empty list."""
    path = _replies_path(session_id)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def append_reply(session_id: str, turn: int, question: str, user_reply: str) -> None:
    """Append one Q&A exchange to the replies log."""
    _ensure_session_dir()
    path = _replies_path(session_id)
    replies = load_replies(session_id)
    replies.append({
        "turn": turn,
        "question": question,
        "user_reply": user_reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(replies, f, indent=2)


def create_new_session(conversation_id: str = "") -> tuple[str, PreUploadContract]:
    """Create a new session with a fresh contract. Returns (session_id, contract)."""
    session_id = generate_session_id()
    now = datetime.now(timezone.utc).isoformat()
    contract = PreUploadContract(
        conversation=ConversationMeta(
            session_id=session_id,
            conversation_id=conversation_id or session_id,
            timestamp=now,
            phase="pre_upload",
            dataset_uploaded=False,
            conversation_turn=1,
        ),
    )
    save_contract(session_id, contract)
    return session_id, contract