"""
plugins/parsers/xml_parser.py - XML Historian & PLC Export Parser Plugin
========================================================================
Stage 2 Parser plugin for XML historian/PLC export files (.xml).
Unpacks structured tabular record sequences using standard xml.etree.ElementTree.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict
import xml.etree.ElementTree as ET
import pandas as pd

from ..base import BaseParserPlugin, MatchResult
from ..context import PipelineContext
from ..registry import register_plugin

logger = logging.getLogger(__name__)


@register_plugin
class XmlParserPlugin(BaseParserPlugin):
    plugin_id = "xml_parser"
    plugin_name = "XML Historian / PLC Export Parser Plugin"
    version = "1.0.0"
    priority = 10

    def probe(self, context: PipelineContext) -> MatchResult:
        xml_files = [item for item in context.inventory if item.format_ext.lower() == ".xml"]
        if xml_files:
            return MatchResult(
                supported=True,
                confidence=0.85,
                reasons=[f"Found {len(xml_files)} XML file(s)"],
                detected_family="xml",
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No XML files in inventory"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        results: Dict[str, pd.DataFrame] = {}
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            records = []
            for elem in root:
                row = {}
                # Capture element attributes
                row.update(elem.attrib)
                # Capture child element tags & text
                for child in elem:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child.text and child.text.strip():
                        row[tag] = child.text.strip()
                    for k, v in child.attrib.items():
                        row[f"{tag}_{k}"] = v
                if not row and elem.text and elem.text.strip():
                    row["value"] = elem.text.strip()
                if row:
                    records.append(row)

            if records:
                df = pd.DataFrame(records)
                results[filepath.stem] = df
        except Exception as e:
            logger.warning(f"[XmlParserPlugin] Failed to parse XML file {filepath}: {e}")

        return results

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext.lower() == ".xml":
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
