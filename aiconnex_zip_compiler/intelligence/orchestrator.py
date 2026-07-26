"""
intelligence/orchestrator.py - Intelligence Layer Orchestrator
==============================================================
Runs the 7 analysis stages in order and emits archive_intelligence_report.json.

Stage split by determinism:
  1. Archive Exploration   - deterministic
  2. Format Detection      - deterministic, LLM only for unknowns
  3. Parser Selection      - LLM (over live plugin catalog)
  4. Metadata Extraction   - deterministic
  5. Schema Discovery      - LLM
  6. Semantic Analysis     - LLM
  7. Problem Discovery     - LLM (generates the HITL question and options)

Graceful degradation: if the LLM is unreachable, deterministic stages still run
and the report is marked degraded=True. The caller decides whether to fall back
to the legacy heuristic path or abort.

Stages 1-3 run BEFORE parsing (they inform which parser to use). Stages 4-7 run
AFTER parsing, because they need real DataFrames to compute statistics from.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .archive_explorer import ArchiveExplorer
from .format_detector import FormatDetector
from .llm_client import LLMClient, llm_disabled_by_env
from .metadata_extractor import MetadataExtractor
from .models import IntelligenceReport, StageStatus
from .parser_advisor import ParserAdvisor
from .problem_discoverer import ProblemDiscoverer
from .schema_analyzer import SchemaAnalyzer
from .semantic_analyzer import SemanticAnalyzer

logger = logging.getLogger(__name__)


class IntelligenceOrchestrator:
    """
    Coordinates all intelligence stages.

    Usage from the compiler:
        orch = IntelligenceOrchestrator()
        orch.run_pre_parse(target_path, temp_dir, registry)   # stages 1-3
        # ... compiler parses files into DataFrames ...
        orch.run_post_parse(parsed_tables)                    # stages 4-7
        orch.write_report(output_dir)
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        enable_llm: bool = True,
    ) -> None:
        if enable_llm and llm_disabled_by_env():
            logger.info(
                "[Intelligence] LLM disabled via environment - running deterministic stages only"
            )
            enable_llm = False

        self.llm = llm_client if llm_client is not None else (LLMClient() if enable_llm else None)
        self.enable_llm = enable_llm

        if self.llm is not None and not self.llm.is_available():
            logger.warning(
                "[Intelligence] Ollama not reachable - LLM stages will be skipped "
                "and the report will be marked degraded"
            )
            self.llm = None

        self.report: Optional[IntelligenceReport] = None
        self._explorer = ArchiveExplorer()
        self._format_detector = FormatDetector(self.llm)
        self._parser_advisor = ParserAdvisor(self.llm)
        self._metadata_extractor = MetadataExtractor()
        self._schema_analyzer = SchemaAnalyzer(self.llm)
        self._semantic_analyzer = SemanticAnalyzer(self.llm)
        self._problem_discoverer = ProblemDiscoverer(self.llm)

    # -- Stages 1-3 (pre-parse) --------------------------------------------

    def run_pre_parse(
        self,
        target_path: Path,
        temp_dir: Path,
        registry: Any = None,
    ) -> IntelligenceReport:
        """Run archive exploration, format detection, and parser selection."""
        target_path = Path(target_path)
        mode = "llm_enhanced" if self.llm is not None else "deterministic_headless"
        self.report = IntelligenceReport(
            archive_name=target_path.name,
            llm_available=self.llm is not None,
            execution_mode=mode,
        )

        # Stage 1: Archive Exploration
        with self._stage("archive_exploration") as status:
            extract_root = Path(temp_dir) / "intel_extracted"
            self.report.archive_tree = self._explorer.explore(target_path, extract_root)
            logger.info(
                f"[Intelligence] Stage 1: {len(self.report.archive_tree.nodes)} files, "
                f"max depth {self.report.archive_tree.max_depth}, "
                f"{self.report.archive_tree.nested_archive_count} nested archives"
            )

        # Stage 2: Format Detection
        with self._stage("format_detection") as status:
            if self.report.archive_tree:
                self.report.fingerprints = self._format_detector.detect(
                    self.report.archive_tree.nodes
                )
                status.used_llm = self._format_detector.used_llm
                status.llm_model = self._format_detector.llm_model_used
                distinct = {f.detected_format for f in self.report.fingerprints}
                logger.info(f"[Intelligence] Stage 2: formats detected {sorted(distinct)}")

        # Stage 3: Parser Selection
        with self._stage("parser_selection") as status:
            if self.report.fingerprints and registry is not None:
                catalog = ParserAdvisor.build_plugin_catalog(registry)
                self.report.parser_decisions = self._parser_advisor.advise(
                    self.report.fingerprints, catalog
                )
                status.used_llm = self._parser_advisor.used_llm
                status.llm_model = self._parser_advisor.llm_model_used

                needs_new = [
                    d.detected_format
                    for d in self.report.parser_decisions
                    if d.requires_new_plugin
                ]
                if needs_new:
                    logger.warning(
                        f"[Intelligence] Stage 3: formats needing NEW plugins: {needs_new}"
                    )

        return self.report

    # -- Stages 4-7 (post-parse) -------------------------------------------

    def run_post_parse(
        self,
        parsed_tables: Dict[str, pd.DataFrame],
        source_paths: Optional[Dict[str, str]] = None,
    ) -> IntelligenceReport:
        """Run metadata extraction, schema discovery, semantics, problem discovery."""
        if self.report is None:
            mode = "llm_enhanced" if self.llm is not None else "deterministic_headless"
            self.report = IntelligenceReport(
                archive_name="unknown",
                llm_available=self.llm is not None,
                execution_mode=mode,
            )

        # Stage 4: Metadata Extraction
        with self._stage("metadata_extraction"):
            self.report.table_metadata = self._metadata_extractor.extract_all(
                parsed_tables, source_paths
            )
            total_cols = sum(t.column_count for t in self.report.table_metadata)
            logger.info(
                f"[Intelligence] Stage 4: profiled {len(self.report.table_metadata)} tables, "
                f"{total_cols} columns"
            )

        # Stage 5: Schema Discovery
        with self._stage("schema_discovery") as status:
            roles, relationships = self._schema_analyzer.analyze(self.report.table_metadata)
            self.report.schema_roles = roles
            self.report.relationships = relationships
            status.used_llm = self._schema_analyzer.used_llm
            status.llm_model = self._schema_analyzer.llm_model_used
            logger.info(
                f"[Intelligence] Stage 5: {len(roles)} table role sets, "
                f"{len(relationships)} relationships"
            )

        # Stage 7 (Pass 1): Problem Discovery - establish domain & target hypothesis first
        with self._stage("problem_discovery") as status:
            self.report.problem_hypothesis = self._problem_discoverer.discover(
                self.report.archive_tree,
                self.report.table_metadata,
                self.report.schema_roles,
                self.report.relationships,
                self.report.semantic_labels,
            )
            status.used_llm = self._problem_discoverer.used_llm
            status.llm_model = self._problem_discoverer.llm_model_used

            if self.report.problem_hypothesis:
                hypothesis = self.report.problem_hypothesis
                logger.info(
                    f"[Intelligence] Stage 7 (Pass 1): domain='{hypothesis.domain}', "
                    f"{len(hypothesis.detected_partitions)} partitions, "
                    f"{len(hypothesis.intent_options)} options generated"
                )

        # Stage 6 (Pass 2): Semantic Analysis - consume established domain context
        with self._stage("semantic_analysis") as status:
            domain_hint = None
            if self.report.problem_hypothesis:
                domain_hint = self.report.problem_hypothesis.domain

            self.report.semantic_labels = self._semantic_analyzer.analyze(
                self.report.table_metadata,
                self.report.schema_roles,
                domain_hint=domain_hint,
            )
            status.used_llm = self._semantic_analyzer.used_llm
            status.llm_model = self._semantic_analyzer.llm_model_used
            logger.info(f"[Intelligence] Stage 6 (Pass 2): {len(self.report.semantic_labels)} columns labelled")

        return self.report

    # -- Report emission ---------------------------------------------------

    def write_report(self, output_dir: Path) -> Optional[Path]:
        """Write archive_intelligence_report.json into the output directory."""
        if self.report is None:
            return None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "archive_intelligence_report.json"

        try:
            report_path.write_text(
                json.dumps(self.report.to_dict(), indent=2, default=str), encoding="utf-8"
            )
            logger.info(f"[Intelligence] Report written: {report_path}")
            return report_path
        except Exception as e:
            logger.warning(f"[Intelligence] Failed to write report: {e}")
            return None

    # -- Stage instrumentation ---------------------------------------------

    def _stage(self, stage_name: str):
        """Context manager that records timing/success for a stage."""
        return _StageRecorder(self, stage_name)


class _StageRecorder:
    """Records a StageStatus onto the report, capturing errors without aborting."""

    def __init__(self, orchestrator: IntelligenceOrchestrator, stage_name: str) -> None:
        self.orchestrator = orchestrator
        self.status = StageStatus(stage_name=stage_name, succeeded=False)
        self._t0 = 0.0

    def __enter__(self) -> StageStatus:
        self._t0 = time.time()
        return self.status

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.status.duration_seconds = round(time.time() - self._t0, 3)

        if exc_type is not None:
            self.status.succeeded = False
            self.status.error = f"{exc_type.__name__}: {exc_value}"
            logger.warning(
                f"[Intelligence] Stage '{self.status.stage_name}' failed: {self.status.error}"
            )
            if self.orchestrator.report is not None:
                self.orchestrator.report.degraded = True
        else:
            self.status.succeeded = True

        if self.orchestrator.report is not None:
            self.orchestrator.report.stage_statuses.append(self.status)

        # Suppress the exception - intelligence failures must never abort compilation
        return True
