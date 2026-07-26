"""
plugins/parsers/json_parser.py - JSON & JSON-Lines Data Parser Plugin
======================================================================
Stage 2 Parser plugin for JSON, JSON-Lines, and NDJSON files (.json, .jsonl, .ndjson).
Parses standard array/object JSON as well as line-delimited stream logs into DataFrames.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)


@register_plugin
class JsonParserPlugin(BaseParserPlugin):
    plugin_id = "json_parser"
    plugin_name = "JSON / JSONL Data Parser Plugin"
    version = "1.0.0"
    priority = 12

    def probe(self, context: PipelineContext) -> MatchResult:
        json_files = [
            item for item in context.inventory
            if item.format_ext.lower() in [".json", ".jsonl", ".ndjson"]
        ]
        if json_files:
            return MatchResult(
                supported=True,
                confidence=0.90,
                reasons=[f"Found {len(json_files)} JSON/JSONL file(s)"],
                detected_family="json",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No JSON files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        ext = filepath.suffix.lower()

        try:
            if ext in [".jsonl", ".ndjson"]:
                df = pd.read_json(filepath, lines=True)
                if not df.empty:
                    results[filepath.stem] = df
            else:
                # Standard .json file
                try:
                    df = pd.read_json(filepath)
                    if not df.empty:
                        results[filepath.stem] = df
                        return results
                except Exception:
                    pass

                # Fallback manual json parse & normalize
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    if not df.empty:
                        results[filepath.stem] = df
                elif isinstance(data, dict):
                    # Check if dictionary contains multiple tables
                    dict_tables = {}
                    for k, v in data.items():
                        if isinstance(v, list) and v and isinstance(v[0], dict):
                            dict_tables[f"{filepath.stem}_{k}"] = pd.DataFrame(v)

                    if dict_tables:
                        results.update(dict_tables)
                    else:
                        df = pd.json_normalize(data)
                        if not df.empty:
                            results[filepath.stem] = df
        except Exception as e:
            logger.warning(f"[JsonParserPlugin] Failed to parse JSON file {filepath}: {e}")

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext.lower() in [".json", ".jsonl", ".ndjson"]:
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
