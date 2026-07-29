"""
aiconnex_agent/memory/backends/base.py
=========================================
SemanticMemoryBackend interface. Sits BEHIND the Entity memory layer only -
Decision and Procedural memory never call this. Any implementation (fake,
mem0, or otherwise) must satisfy this contract so memory_builder.py and
memory_agent.py never need to know which concrete backend is active.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SemanticMemoryBackend(ABC):
    """Fuzzy semantic search interface over Entity memory observations."""

    @abstractmethod
    def add(self, text: str, metadata: Dict[str, Any]) -> None:
        """Index one piece of text with associated metadata (e.g. subject_id, subject_type)."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Return up to `limit` results, each shaped {"text": str, "metadata": dict, "score": float}."""
        raise NotImplementedError
