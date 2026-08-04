"""
Loader for the Data Dictionary module.

Loads seed JSON into the store at startup. This module is called once
from app.py during initialization.
"""

from __future__ import annotations

import os

from dictionary.store import initialize


def load_dictionary() -> None:
    """Load all dictionary data into the in-memory store.

    Call this once at app startup, before any requests are handled.
    """
    initialize()