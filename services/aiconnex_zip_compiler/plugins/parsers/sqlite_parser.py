"""
plugins/parsers/sqlite_parser.py - SQLite Database Parser Plugin
===================================================================
Stage 2 Parser plugin for SQLite database files (.db, .sqlite, .sqlite3).
Extracts stored user tables using standard Python sqlite3 into pandas DataFrames.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sqlite3
from typing import Dict
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)


@register_plugin
class SqliteParserPlugin(BaseParserPlugin):
    plugin_id = "sqlite_parser"
    plugin_name = "SQLite Database Parser Plugin"
    version = "1.0.0"
    priority = 15

    def probe(self, context: PipelineContext) -> MatchResult:
        db_files = [
            item for item in context.inventory
            if item.format_ext.lower() in [".db", ".sqlite", ".sqlite3"]
        ]
        if db_files:
            return MatchResult(
                supported=True,
                confidence=0.95,
                reasons=[f"Found {len(db_files)} SQLite database file(s)"],
                detected_family="sqlite",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No SQLite files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        conn = None
        try:
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            rows = cursor.fetchall()
            tables = [row[0] for row in rows if not row[0].startswith("sqlite_")]

            for tbl in tables:
                df = pd.read_sql_query(f'SELECT * FROM "{tbl}"', conn)
                key = f"{filepath.stem}_{tbl}" if len(tables) > 1 or tbl != filepath.stem else filepath.stem
                results[key] = df
        except Exception as e:
            logger.warning(f"[SqliteParserPlugin] Failed to read SQLite database {filepath}: {e}")
        finally:
            if conn:
                conn.close()

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext.lower() in [".db", ".sqlite", ".sqlite3"]:
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
