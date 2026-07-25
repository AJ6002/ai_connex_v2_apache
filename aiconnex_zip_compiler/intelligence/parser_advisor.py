"""
intelligence/parser_advisor.py - Stage 3: LLM-Driven Parser Selection
=====================================================================
Decides HOW each detected format should be read, by reasoning over:
  - the detected formats from Stage 2
  - the live capability catalog of registered parser plugins

Critically, the plugin catalog is introspected from the PluginRegistry at
runtime - it is not a hardcoded list. When a new plugin is promoted by the
Scout Agent, it automatically appears in the catalog on the next run.

Outcomes per format:
  - chosen_plugin_id set        -> an existing plugin can read it
  - requires_new_plugin = True  -> handed to the Scout Agent with a proposed
                                   approach and fallback chain
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient, LLMUnavailableError
from .models import FileFingerprint, ParserDecision
from .validation import safe_confidence

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a data ingestion architect deciding how to read files into pandas DataFrames.

You receive:
  1. A list of detected file formats found inside a dataset archive.
  2. A catalog of parser plugins currently available in the compiler, each with
     the file extensions and format families it declares it can handle.

For EACH detected format, decide whether an existing plugin can read it, or
whether a new plugin must be written.

Respond with ONLY a JSON object in exactly this shape:
{
  "decisions": [
    {
      "detected_format": "<echo the format id given>",
      "chosen_plugin_id": "<plugin_id from the catalog, or null if none can handle it>",
      "requires_new_plugin": false,
      "proposed_plugin_stage": "parser",
      "proposed_approach": "<if requires_new_plugin, describe the reading strategy in 1-3 sentences, else null>",
      "fallback_chain": ["<ordered python approaches to try, e.g. numpy.fromfile, struct.unpack>"],
      "confidence": 0.9,
      "reasoning": "<one sentence>"
    }
  ]
}

Rules:
- Only use plugin_id values that appear in the provided catalog. Never invent one.
- Set requires_new_plugin true ONLY when no catalog plugin can plausibly read the format.
- Formats that are documentation or images (pdf, png, jpeg) are not tabular data:
  set chosen_plugin_id null, requires_new_plugin false, and note that in reasoning.
- Container formats already unpacked upstream (zip_container, gzip, bzip2, xz,
  tar) need no parser: chosen_plugin_id null, requires_new_plugin false.
- fallback_chain may be an empty list when a plugin handles the format directly.
- confidence is a float 0.0-1.0."""

# Formats that are structurally not tabular data and need no parser at all.
NON_TABULAR_FORMATS = {
    "pdf", "png", "jpeg", "gif", "webp", "bmp", "tiff",
    "zip_container", "gzip", "bzip2", "xz", "tar",
    "plain_text", "empty_text", "unknown",
}


class ParserAdvisor:
    """Maps detected formats to parser plugins using LLM reasoning."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client
        self.llm_model_used: Optional[str] = None
        self.used_llm = False

    def advise(
        self,
        fingerprints: List[FileFingerprint],
        plugin_catalog: List[Dict[str, Any]],
    ) -> List[ParserDecision]:
        """
        Produce one ParserDecision per distinct detected format.

        Parameters
        ----------
        fingerprints : list of FileFingerprint
            Output of Stage 2.
        plugin_catalog : list of dict
            Live registry introspection: [{plugin_id, stage, priority,
            handles_extensions, description}, ...]
        """
        grouped = self._group_by_format(fingerprints)
        if not grouped:
            return []

        decisions = [
            ParserDecision(detected_format=fmt, affected_paths=paths)
            for fmt, paths in grouped.items()
        ]

        # Formats we can resolve structurally without consulting the LLM
        pending: List[ParserDecision] = []
        for decision in decisions:
            if decision.detected_format in NON_TABULAR_FORMATS:
                decision.chosen_plugin_id = None
                decision.requires_new_plugin = False
                decision.confidence = 0.95
                decision.llm_reasoning = "Non-tabular or already-unpacked container format; no parser required."
            else:
                pending.append(decision)

        if pending and self.llm is not None:
            self._resolve_with_llm(pending, plugin_catalog)
        elif pending:
            logger.warning("[ParserAdvisor] No LLM client - parser decisions left unresolved")

        return decisions

    # -- Internals ---------------------------------------------------------

    @staticmethod
    def _group_by_format(fingerprints: List[FileFingerprint]) -> Dict[str, List[str]]:
        grouped: Dict[str, List[str]] = {}
        for fp in fingerprints:
            grouped.setdefault(fp.detected_format, []).append(fp.relative_path)
        return grouped

    def _resolve_with_llm(
        self,
        pending: List[ParserDecision],
        plugin_catalog: List[Dict[str, Any]],
    ) -> None:
        payload = {
            "detected_formats": [
                {
                    "detected_format": d.detected_format,
                    "file_count": len(d.affected_paths),
                    "example_paths": d.affected_paths[:5],
                }
                for d in pending
            ],
            "available_plugins": plugin_catalog,
        }

        user_prompt = (
            "Decide how to read each detected format.\n\n"
            + json.dumps(payload, indent=2)
        )

        try:
            response = self.llm.complete_json(SYSTEM_PROMPT, user_prompt)
        except LLMUnavailableError as e:
            logger.warning(f"[ParserAdvisor] LLM unavailable: {e}")
            return

        self.used_llm = True
        self.llm_model_used = response.model_used

        raw_decisions = response.data.get("decisions", [])
        if not isinstance(raw_decisions, list):
            logger.warning("[ParserAdvisor] LLM returned unexpected shape for 'decisions'")
            return

        valid_plugin_ids = {str(p.get("plugin_id")) for p in plugin_catalog if p.get("plugin_id")}
        answers = {
            str(item.get("detected_format")): item
            for item in raw_decisions
            if isinstance(item, dict) and item.get("detected_format")
        }

        for decision in pending:
            answer = answers.get(decision.detected_format)
            if not answer:
                logger.debug(
                    f"[ParserAdvisor] LLM gave no decision for '{decision.detected_format}'"
                )
                continue

            chosen = answer.get("chosen_plugin_id")
            # Guard against hallucinated plugin ids
            if chosen and str(chosen) not in valid_plugin_ids:
                logger.warning(
                    f"[ParserAdvisor] LLM proposed unknown plugin_id '{chosen}' for "
                    f"'{decision.detected_format}' - treating as requires_new_plugin"
                )
                chosen = None
                decision.requires_new_plugin = True
            else:
                decision.requires_new_plugin = bool(answer.get("requires_new_plugin", False))

            decision.chosen_plugin_id = str(chosen) if chosen else None
            decision.proposed_plugin_stage = answer.get("proposed_plugin_stage") or (
                "parser" if decision.requires_new_plugin else None
            )
            decision.proposed_approach = answer.get("proposed_approach")
            decision.llm_reasoning = answer.get("reasoning")

            fallback = answer.get("fallback_chain")
            if isinstance(fallback, list):
                decision.fallback_chain = [str(f) for f in fallback][:6]

            decision.confidence = safe_confidence(answer.get("confidence"))

    # -- Registry introspection --------------------------------------------

    @staticmethod
    def build_plugin_catalog(registry: Any) -> List[Dict[str, Any]]:
        """
        Introspect the live PluginRegistry into an LLM-readable catalog.

        Reads real attributes off registered plugin instances so newly promoted
        Scout Agent plugins are included automatically.
        """
        catalog: List[Dict[str, Any]] = []

        for stage in ("discovery", "parser", "assembler", "harvester", "normalizer"):
            try:
                plugins = registry.get_plugins(stage)
            except Exception as e:
                logger.debug(f"[ParserAdvisor] Could not list plugins for stage '{stage}': {e}")
                continue

            for plugin in plugins:
                entry: Dict[str, Any] = {
                    "plugin_id": getattr(plugin, "plugin_id", "unknown"),
                    "stage": stage,
                    "priority": getattr(plugin, "priority", 0),
                    "version": getattr(plugin, "version", "0.0.0"),
                    "description": (getattr(plugin, "plugin_name", "") or "").strip(),
                }

                # Extract declared extensions if the plugin exposes them
                extensions = getattr(plugin, "supported_extensions", None)
                if extensions:
                    entry["handles_extensions"] = sorted(str(e) for e in extensions)
                else:
                    entry["handles_extensions"] = ParserAdvisor._infer_extensions_from_doc(plugin)

                catalog.append(entry)

        return catalog

    @staticmethod
    def _infer_extensions_from_doc(plugin: Any) -> List[str]:
        """
        Pull extension hints out of the plugin's docstring as a last resort.
        Structural text scan only - no hardcoded plugin-to-extension mapping.
        """
        import re

        doc = (getattr(plugin, "__doc__", "") or "") + " " + (getattr(plugin, "plugin_name", "") or "")
        found = re.findall(r"\.[a-z0-9]{1,6}\b", doc.lower())
        # Filter out things that look like sentence-ending or version fragments
        noise = {".py", ".e", ".g", ".0", ".1", ".2", ".3"}
        return sorted({f for f in found if f not in noise})
