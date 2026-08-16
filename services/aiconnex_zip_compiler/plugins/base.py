"""
plugins/base.py - Abstract Base Classes & Core Interfaces for Compiler Plugins
================================================================================
Defines the base plugin contracts, probe MatchResult structures, and 5 pipeline stage ABCs:
  Stage 1: BaseDiscoveryPlugin
  Stage 2: BaseParserPlugin
  Stage 3: BaseAssemblerPlugin
  Stage 4: BaseFeatureHarvesterPlugin
  Stage 5: BaseSchemaNormalizerPlugin
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from .context import PipelineContext


@dataclass
class MatchResult:
    """Returned by every plugin's probe() method for deterministic selection."""
    supported: bool
    confidence: float          # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
    detected_family: Optional[str] = None


class BasePlugin(ABC):
    """Common interface for all compiler plugins."""
    plugin_id: str             # Stable identifier (e.g. "csv_parser", "scada_excel_parser")
    plugin_name: str           # Human-readable name
    version: str = "1.0.0"     # Semantic version (e.g. "1.2.0")
    contract_version: int = 1  # Plugin API contract version
    stage: str                 # "discovery" | "parser" | "assembler" | "harvester" | "normalizer"
    priority: int = 10         # Higher wins after policy override (0-100)

    @abstractmethod
    def probe(self, context: PipelineContext) -> MatchResult:
        """Non-destructive inspection: can this plugin handle the given pipeline context?"""
        pass

    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute plugin logic and return updated PipelineContext."""
        pass


class BaseDiscoveryPlugin(BasePlugin):
    """Stage 1: Container & Layout Discovery Plugin."""
    stage: str = "discovery"

    @abstractmethod
    def discover(self, target_path: Path, context: PipelineContext) -> PipelineContext:
        """Walk archive/directory and populate file inventory and layout metadata."""
        pass

    def execute(self, context: PipelineContext) -> PipelineContext:
        return self.discover(context.target_path, context)


class BaseParserPlugin(BasePlugin):
    """Stage 2: File Format Reader Plugin (CSV, Excel, HDF5, MAT, Parquet, TXT)."""
    stage: str = "parser"

    @abstractmethod
    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        """Read single raw file and return named DataFrames."""
        pass

    def execute(self, context: PipelineContext) -> PipelineContext:
        # Default executor iterates through context inventory matching this parser
        return context


class BaseAssemblerPlugin(BasePlugin):
    """Stage 3: Multi-Table Assembler / Joiner Plugin (Relational, Vertical Stack)."""
    stage: str = "assembler"

    @abstractmethod
    def assemble(self, parsed_tables: Dict[str, pd.DataFrame], context: PipelineContext) -> Dict[str, pd.DataFrame]:
        """Merge, stack, or join parsed DataFrames into logical datasets."""
        pass

    def execute(self, context: PipelineContext) -> PipelineContext:
        assembled = self.assemble(context.parsed_tables, context)
        context.assembled_tables.update(assembled)
        return context


class BaseFeatureHarvesterPlugin(BasePlugin):
    """Stage 4: Dense Signal / Snapshot Feature Harvester Plugin."""
    stage: str = "harvester"

    @abstractmethod
    def harvest(self, tables: Dict[str, pd.DataFrame], context: PipelineContext) -> Dict[str, pd.DataFrame]:
        """Summarize raw high-frequency signals or cycle arrays into feature rows."""
        pass

    def execute(self, context: PipelineContext) -> PipelineContext:
        harvested = self.harvest(context.parsed_tables, context)
        context.harvested_tables.update(harvested)
        return context


class BaseSchemaNormalizerPlugin(BasePlugin):
    """Stage 5: Canonical Schema & Timestamp Normalizer Plugin."""
    stage: str = "normalizer"

    @abstractmethod
    def normalize(self, df: pd.DataFrame, context: PipelineContext) -> pd.DataFrame:
        """Map column headers and timestamps to canonical ML pipeline schema."""
        pass

    def execute(self, context: PipelineContext) -> PipelineContext:
        # Normalize assembled tables first, then harvested if assembled is empty
        target_tables = context.assembled_tables or context.harvested_tables or context.parsed_tables
        for k, df in list(target_tables.items()):
            context.normalized_tables[k] = self.normalize(df, context)
        return context
