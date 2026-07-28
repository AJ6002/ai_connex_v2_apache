"""
intelligence/validation.py - Shared LLM Output Validation Helpers
===================================================================
Every stage that parses an LLM JSON response uses these helpers so the same
safety rules apply everywhere, instead of each stage re-implementing its own
(sometimes incomplete) checks.

Two responsibilities:
  1. safe_confidence()  - LLMs sometimes return confidence values outside
                           0.0-1.0 (or non-numeric junk). Clamp/coerce instead
                           of trusting the raw value.
  2. safe_choice()       - When the prompt asks for one of a fixed set of
                           values (e.g. output_mode, join_strategy) and the
                           LLM returns something outside that set, coerce to
                           an explicit default rather than passing the
                           unexpected value further down the pipeline.
  3. stable_slug()       - Deterministic identifier derived from structural
                           fields, NOT from LLM-chosen wording. Used to build
                           option_id values that stay the same across runs
                           for the same underlying choice.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional, Set


def safe_confidence(value: Any, default: float = 0.0) -> float:
    """Coerce a value to a float and clamp it into [0.0, 1.0]."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:  # NaN check without importing math
        return default
    return max(0.0, min(1.0, parsed))


def safe_choice(value: Any, allowed: Set[str], default: str) -> str:
    """Return `value` if it is one of `allowed`, else `default`."""
    text = str(value) if value is not None else ""
    return text if text in allowed else default


def slugify(text: str) -> str:
    """Lowercase, ASCII, underscore-joined slug of arbitrary text."""
    slug = re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")
    return slug or "option"


def stable_slug(*parts: Optional[str]) -> str:
    """
    Build a deterministic slug from an ORDERED sequence of structural values
    (e.g. output_mode, merge_strategy, target_column). Empty/None parts are
    skipped. Two calls with the same structural inputs always produce the
    same slug, regardless of anything the LLM invented in free text.
    """
    cleaned = [slugify(p) for p in parts if p]
    return "_".join(cleaned) if cleaned else "option"


def dedupe_with_suffix(candidate: str, seen: Set[str]) -> str:
    """
    Return `candidate` if unused, otherwise `candidate_2`, `candidate_3`, ...
    Mutates `seen` by adding the returned value.
    """
    if candidate not in seen:
        seen.add(candidate)
        return candidate

    suffix = 2
    while f"{candidate}_{suffix}" in seen:
        suffix += 1
    resolved = f"{candidate}_{suffix}"
    seen.add(resolved)
    return resolved
