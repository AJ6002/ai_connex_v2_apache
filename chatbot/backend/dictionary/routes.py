"""
Flask blueprint for the Data Dictionary module.

Exposes the dictionary's HTTP surface. All write operations go through
store.py, which enforces the entry_type="feature" rejection rule.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from dictionary.schemas import DictionaryEntry
from dictionary.store import get_entry, list_entries, upsert_entry, delete_entry

bp = Blueprint("dictionary", __name__, url_prefix="/api/dictionary")


@bp.route("/entries", methods=["GET"])
def list_entries_route():
    """List dictionary entries, optionally filtered by entry_type.

    Query params:
        entry_type (optional): Filter to a specific entry type
    """
    entry_type = request.args.get("entry_type")
    entries = list_entries(entry_type=entry_type)
    return jsonify([e.model_dump() for e in entries])


@bp.route("/entries/<entry_id>", methods=["GET"])
def get_entry_route(entry_id: str):
    """Get a single dictionary entry by ID."""
    entry = get_entry(entry_id)
    if entry is None:
        return jsonify({"error": f"Entry '{entry_id}' not found"}), 404
    return jsonify(entry.model_dump())


@bp.route("/entries", methods=["POST"])
def upsert_entry_route():
    """Create or update a content-source entry.

    Rejects entry_type="feature" — features must be edited via the seed file.
    """
    data = request.get_json(force=True) or {}
    try:
        entry = DictionaryEntry.model_validate(data)
    except Exception as exc:
        return jsonify({"error": f"Invalid entry data: {exc}"}), 400

    try:
        result = upsert_entry(entry)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 403

    return jsonify(result.model_dump()), 201


@bp.route("/entries/<entry_id>", methods=["DELETE"])
def delete_entry_route(entry_id: str):
    """Delete a content-source entry by ID.

    Rejects deletion of entry_type="feature" entries.
    """
    try:
        deleted = delete_entry(entry_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 403

    if not deleted:
        return jsonify({"error": f"Entry '{entry_id}' not found"}), 404
    return jsonify({"deleted": entry_id}), 200