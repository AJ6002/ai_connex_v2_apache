"""
Data Dictionary store — the ONLY module allowed to read/write the dictionary
directly. All other files (including routes.py) must call these functions.

Follows the swappable-store pattern from pipeline_state.py: in-memory dicts
backed by JSON files on disk.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from dictionary.schemas import DictionaryEntry, EntryType

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────

_BASE_DIR = os.path.dirname(__file__)
_SEED_PATH = os.path.join(_BASE_DIR, "seed", "feature_dictionary.json")
_DATA_PATH = os.path.join(_BASE_DIR, "..", "data", "dictionary_entries.json")

# Ensure data directory exists
os.makedirs(os.path.dirname(_DATA_PATH), exist_ok=True)

# ──────────────────────────────────────────────
# In-memory stores
# ──────────────────────────────────────────────

# Feature entries: loaded from seed file at startup, never written at runtime
_FEATURE_STORE: dict[str, DictionaryEntry] = {}

# Content-source entries: loaded from data file, rewritten on every write
_CONTENT_STORE: dict[str, DictionaryEntry] = {}


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────


def _load_feature_seed() -> None:
    """Load feature entries from seed JSON into the in-memory dict."""
    global _FEATURE_STORE
    if not os.path.exists(_SEED_PATH):
        _FEATURE_STORE = {}
        return
    try:
        with open(_SEED_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _FEATURE_STORE = {}
        for item in raw:
            entry = DictionaryEntry.model_validate(item)
            _FEATURE_STORE[entry.entry_id] = entry
    except (json.JSONDecodeError, FileNotFoundError):
        _FEATURE_STORE = {}


def _load_content_store() -> None:
    """Load content-source entries from data JSON into the in-memory dict."""
    global _CONTENT_STORE
    if not os.path.exists(_DATA_PATH):
        _CONTENT_STORE = {}
        return
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _CONTENT_STORE = {}
        for item in raw:
            entry = DictionaryEntry.model_validate(item)
            _CONTENT_STORE[entry.entry_id] = entry
    except (json.JSONDecodeError, FileNotFoundError):
        _CONTENT_STORE = {}


def _persist_content_store() -> None:
    """Rewrite the content-source JSON file from the in-memory dict."""
    entries = list(_CONTENT_STORE.values())
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([e.model_dump() for e in entries], f, indent=2)


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────


def get_entry(entry_id: str) -> Optional[DictionaryEntry]:
    """Look up any entry by ID (feature or content-source)."""
    return _FEATURE_STORE.get(entry_id) or _CONTENT_STORE.get(entry_id)


def list_entries(entry_type: str | None = None) -> list[DictionaryEntry]:
    """List entries, optionally filtered by entry_type.

    If entry_type is None, returns all entries from both stores.
    """
    if entry_type is None:
        return list(_FEATURE_STORE.values()) + list(_CONTENT_STORE.values())
    return [
        e for e in list(_FEATURE_STORE.values()) + list(_CONTENT_STORE.values())
        if e.entry_type == entry_type
    ]


def upsert_entry(entry: DictionaryEntry) -> DictionaryEntry:
    """Create or update a content-source entry.

    Raises ValueError if entry_type == "feature" — features are edited via
    the seed file, not through this API.
    """
    if entry.entry_type == "feature":
        raise ValueError(
            "Cannot upsert entry_type='feature' through the API. "
            "Edit seed/feature_dictionary.json and redeploy instead."
        )
    _CONTENT_STORE[entry.entry_id] = entry
    _persist_content_store()
    return entry


def delete_entry(entry_id: str) -> bool:
    """Delete a content-source entry by ID.

    Raises ValueError if the entry is entry_type="feature".
    Returns True if deleted, False if not found.
    """
    entry = _CONTENT_STORE.get(entry_id)
    if entry is None:
        # Also check feature store to give a clear error
        if entry_id in _FEATURE_STORE:
            raise ValueError(
                f"Cannot delete entry_id='{entry_id}' because it is entry_type='feature'. "
                "Features are managed via seed/feature_dictionary.json."
            )
        return False
    if entry.entry_type == "feature":
        raise ValueError(
            f"Cannot delete entry_id='{entry_id}' because it is entry_type='feature'. "
            "Features are managed via seed/feature_dictionary.json."
        )
    del _CONTENT_STORE[entry_id]
    _persist_content_store()
    return True


def initialize() -> None:
    """Load both stores from disk. Call this at app startup."""
    _load_feature_seed()
    _load_content_store()