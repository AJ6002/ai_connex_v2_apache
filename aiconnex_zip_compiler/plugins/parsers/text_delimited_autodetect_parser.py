"""
plugins/parsers/text_delimited_autodetect_parser.py - Text Delimited Autodetect Parser Plugin
=============================================================================================
Stage 2 Parser plugin for raw text/sensor dumps (.dat, .asc, .log, .txt).
Autodetects common delimiters (comma, tab, pipe, semicolon, space) and comment-prefixed headers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional, List
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)


@register_plugin
class TextDelimitedAutodetectParserPlugin(BaseParserPlugin):
    plugin_id = "text_delimited_autodetect_parser"
    plugin_name = "Text Delimited Autodetect Parser Plugin"
    version = "1.0.0"
    priority = 8

    def probe(self, context: PipelineContext) -> MatchResult:
        text_files = [
            item for item in context.inventory
            if item.format_ext.lower() in [".dat", ".asc", ".log", ".txt"]
        ]
        if text_files:
            return MatchResult(
                supported=True,
                confidence=0.80,
                reasons=[f"Found {len(text_files)} text-delimited sensor file(s)"],
                detected_family="text_delimited",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No text-delimited files in inventory"])

    def _autodetect_delimiter(self, lines: List[str]) -> Optional[str]:
        # Filter lines
        data_lines = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            # Strip comment markers for delimiter counting
            uncommented = s.lstrip("#/% ;").strip()
            if uncommented:
                data_lines.append(uncommented)

        if not data_lines:
            return None

        candidates = [",", "\t", "|", ";"]
        best_delim = None
        max_count = 0

        sample = data_lines[:20]
        for delim in candidates:
            counts = [line.count(delim) for line in sample if delim in line]
            if counts:
                avg_count = sum(counts) / len(sample)
                if avg_count > max_count:
                    max_count = avg_count
                    best_delim = delim

        if best_delim:
            return best_delim

        # Fallback to whitespace / space
        return r"\s+"

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            if not lines:
                return results

            sep = self._autodetect_delimiter(lines) or r"\s+"

            # Detect if a comment line acts as a header (e.g. "# timestamp|channel|value")
            header_names = None
            skiprows = 0
            for i, line in enumerate(lines[:20]):
                cleaned = line.strip()
                if not cleaned:
                    continue
                is_comment = any(cleaned.startswith(c) for c in ["#", "//", "%", ";"])
                if is_comment:
                    uncommented = cleaned.lstrip("#/% ;").strip()
                    if sep != r"\s+" and sep in uncommented:
                        parts = [p.strip() for p in uncommented.split(sep)]
                        if len(parts) > 1:
                            header_names = parts
                            skiprows = i + 1
                else:
                    break

            if header_names and skiprows > 0:
                df = pd.read_csv(
                    filepath,
                    sep=sep,
                    engine="python",
                    comment="#",
                    skiprows=skiprows,
                    names=header_names,
                    skipinitialspace=True,
                )
            else:
                df = pd.read_csv(
                    filepath,
                    sep=sep,
                    engine="python",
                    comment="#",
                    skipinitialspace=True,
                )

            if not df.empty:
                results[filepath.stem] = df
        except Exception as e:
            logger.warning(f"[TextDelimitedAutodetectParserPlugin] Failed to read text file {filepath}: {e}")

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext.lower() in [".dat", ".asc", ".log", ".txt"]:
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
