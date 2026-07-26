"""
scout.py - Scout Agent Engine & Compiler Evolution Observer (Layer 3)
====================================================================
Monitors dataset compilation execution, captures failures, analyzes schema
and file structure gaps at the PLUGIN STAGE level, proposes new plugin patches
via LLM, validates in Docker sandbox, and auto-promotes successful plugins
to plugins/ directory. Follows the build -> test -> approve -> rerun cycle.

Logs evolutionary progress to compiler_evolution_log.json.
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .compiler import UnifiedCompiler, CompileResult
from .reporter import classify_compilation_failure, CompilationFailureReport
from .intelligence.models import IntelligenceReport, ProblemHypothesis

logger = logging.getLogger(__name__)


@dataclass
class EvolutionLogEntry:
    timestamp: str
    zip_stem: str
    gap_id: str
    gap_description: str
    target_stage: str
    target_plugin_interface: str
    success: bool
    attempts: int
    patch_applied: Optional[str] = None
    promoted_plugin_path: Optional[str] = None


class ScoutAgent:
    """
    Scout Agent (Layer 3): Plugin-aware self-improving compiler observer.

    Exposes 3 lightweight methods:
      1. inspect(inventory, readme_text) -> IntelligenceReport
      2. advise_strategy(tables, inventory) -> str
      3. self_heal(error_traceback, sample_bytes) -> bool
    """

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path("workspace_data/compiler_evolution_log.json")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def inspect(self, inventory: Any, readme_text: Optional[str] = None) -> IntelligenceReport:
        """
        Inspect dataset inventory and optional readme_text to produce an IntelligenceReport
        mapping column semantics, file structure, and metadata.
        """
        archive_name = "archive"
        if isinstance(inventory, (str, Path)):
            p = Path(inventory)
            archive_name = p.name
            try:
                from .intelligence import IntelligenceOrchestrator
                orch = IntelligenceOrchestrator()
                if p.exists():
                    temp_dir = Path(tempfile.mkdtemp(prefix="scout_inspect_"))
                    try:
                        from .plugins import PluginRegistry
                        reg = PluginRegistry.get_instance()
                        orch.run_pre_parse(target_path=p, temp_dir=temp_dir, registry=reg)
                        return orch.report
                    finally:
                        shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"[ScoutAgent.inspect] IntelligenceOrchestrator pre-parse error: {e}")
        elif isinstance(inventory, list) and len(inventory) > 0:
            first_item = inventory[0]
            if hasattr(first_item, "filepath"):
                archive_name = Path(first_item.filepath).name
            elif isinstance(first_item, (str, Path)):
                archive_name = Path(first_item).name

        report = IntelligenceReport(
            archive_name=archive_name,
            execution_mode="scout_assisted",
        )
        if readme_text:
            report.problem_hypothesis = ProblemHypothesis(
                domain="general_engineering",
                dataset_purpose=readme_text,
            )
        return report

    def advise_strategy(self, tables: Any, inventory: Optional[Any] = None) -> str:
        """
        Recommends compilation strategy (e.g. 'vertical_stack', 'per_partition_batch', 'key_join').
        """
        if isinstance(tables, dict) and len(tables) > 1:
            dfs = list(tables.values())
            col_sets = [set(df.columns) for df in dfs if isinstance(df, pd.DataFrame)]
            if len(col_sets) > 1 and all(s == col_sets[0] for s in col_sets[1:]):
                return "vertical_stack"

            has_time = all(
                any("date" in str(c).lower() or "time" in str(c).lower() for c in s)
                for s in col_sets
            )
            if has_time:
                return "key_join"

        return "vertical_stack"

    def self_heal(
        self,
        error_traceback: str,
        sample_bytes: Optional[bytes] = None,
        zip_path: Optional[Path] = None,
    ) -> bool:
        """
        Generates plugin patch, promotes, and invokes PluginRegistry.get_instance().reload_and_unfreeze().
        """
        logger.info(f"[ScoutAgent.self_heal] Self-healing triggered for traceback:\n{error_traceback[:200]}...")
        try:
            from .plugins import PluginRegistry
            from .reporter import classify_compilation_failure

            target_zip = zip_path or Path("workspace_data/unknown_failure.zip")
            out_dir = Path("workspace_data/unknown_out")
            exc = Exception(error_traceback.split("\n")[-1] if error_traceback else "Compilation Failure")

            report = classify_compilation_failure(target_zip, out_dir, exc)
            promoted = self._attempt_patch_and_promote(report, target_zip)

            registry = PluginRegistry.get_instance()
            registry.reload_and_unfreeze()

            if promoted:
                logger.info(f"[ScoutAgent.self_heal] Successfully promoted patch and reloaded registry: {promoted}")
                return True
            else:
                logger.warning("[ScoutAgent.self_heal] Self-heal attempt did not produce a promoted patch.")
                return False
        except Exception as e:
            logger.warning(f"[ScoutAgent.self_heal] Self-heal execution error: {e}")
            from .plugins import PluginRegistry
            PluginRegistry.get_instance().reload_and_unfreeze()
            return False

    def observe_and_compile(
        self,
        zip_path: Path,
        output_dir: Path,
        max_attempts: int = 3,
    ) -> CompileResult:
        """
        Attempts compilation of a zip archive via plugin pipeline. If it fails,
        observes the failure, classifies gap to a specific plugin stage, generates
        a new plugin class, validates in sandbox, promotes on success, and reruns.
        """
        attempt = 0
        last_result: Optional[CompileResult] = None

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"[ScoutAgent] Compilation attempt {attempt}/{max_attempts} for {zip_path.name}")

            # -- Run compiler (plugin pipeline) -------------------------------
            compiler = UnifiedCompiler(zip_path=zip_path, output_dir=output_dir)
            result = compiler.compile()

            if result.success:
                self._record_evolution(
                    zip_stem=zip_path.stem,
                    gap_id="NONE",
                    gap_desc="Successful compilation",
                    target_stage="none",
                    target_plugin_interface="none",
                    success=True,
                    attempts=attempt,
                    patch_applied="Standard plugin pipeline",
                )
                return result

            last_result = result

            # -- Classify the failure at the plugin stage level ----------------
            error_exc = Exception(result.error or "Unknown compilation error")
            report = classify_compilation_failure(zip_path, output_dir, error_exc)

            logger.warning(
                f"[ScoutAgent] Attempt {attempt} failed: [{report.gap_id}] {report.gap_description} "
                f"(target_stage={report.target_stage}, interface={report.target_plugin_interface})"
            )

            self._record_evolution(
                zip_stem=zip_path.stem,
                gap_id=report.gap_id,
                gap_desc=report.gap_description,
                target_stage=report.target_stage,
                target_plugin_interface=report.target_plugin_interface,
                success=False,
                attempts=attempt,
                patch_applied=f"Gap detected: {report.gap_id}",
            )

            # -- Generate plugin patch via LLM --------------------------------
            promoted_path = self._attempt_patch_and_promote(report, zip_path)
            if promoted_path:
                logger.info(f"[ScoutAgent] Plugin promoted: {promoted_path}. Rerunning compilation...")
                # Reset PluginRegistry to pick up the new plugin
                from .plugins.registry import PluginRegistry
                PluginRegistry.reset_instance()
            else:
                logger.warning(f"[ScoutAgent] Patch generation/promotion failed on attempt {attempt}")

        # Max attempts reached - emit error result
        return last_result or CompileResult(
            input_zip=str(zip_path),
            output_dir=str(output_dir),
            merged_files=[],
            combined_file=None,
            artifacts=None,
            audits=[],
            schema_map=None,
            duration_seconds=0.0,
            success=False,
            error=f"ScoutAgent failed after {max_attempts} attempts.",
        )

    def _attempt_patch_and_promote(
        self,
        report: CompilationFailureReport,
        zip_path: Path,
    ) -> Optional[str]:
        """
        Generate a plugin patch via Ollama LLM, validate in Docker sandbox,
        and promote to plugins/ directory if all gates pass.

        Returns the promoted plugin file path on success, or None on failure.
        """
        try:
            from .patch_proposer import OllamaPatchProposer
            from .sandbox_runner import SandboxRunner

            proposer = OllamaPatchProposer(model_name="gpt-oss:120b-cloud")
            code_patch = proposer.generate_patch(report)

            if not code_patch:
                logger.warning("[ScoutAgent] Patch proposer returned empty patch")
                return None

            # Save patch to workspace for audit trail
            patch_dir = Path("workspace_data/sandbox_patches")
            patch_dir.mkdir(parents=True, exist_ok=True)
            patch_file = patch_dir / f"patch_{report.gap_id}_{zip_path.stem}.py"
            patch_file.write_text(code_patch, encoding="utf-8")

            # -- Docker Sandbox Validation ------------------------------------
            runner = SandboxRunner()
            val_res = runner.validate_patch(code_patch, patch_name=f"patch_{report.gap_id}.py")

            logger.info(
                f"[ScoutAgent] Sandbox result: passed={val_res.regression_passed} "
                f"tier={val_res.tier} ({val_res.passed_test_count}/{val_res.total_test_count} tests)"
            )

            if not val_res.regression_passed:
                logger.warning("[ScoutAgent] Sandbox validation FAILED - patch not promoted")
                return None

            # -- Auto-Promote to plugins/ directory ---------------------------
            promoted_path = self._promote_plugin(code_patch, report)
            return promoted_path

        except Exception as e:
            logger.warning(f"[ScoutAgent] Patch generation/sandbox error: {e}")
            return None

    def _promote_plugin(self, code_patch: str, report: CompilationFailureReport) -> Optional[str]:
        """
        Write validated plugin code to the appropriate plugins/ subdirectory
        based on the target_stage classification.
        """
        stage_to_dir = {
            "parser": "parsers",
            "discovery": "discovery",
            "assembler": "assemblers",
            "harvester": "harvesters",
            "normalizer": "normalizers",
        }

        target_dir_name = stage_to_dir.get(report.target_stage, "parsers")
        plugins_base = Path(__file__).parent / "plugins" / target_dir_name

        if not plugins_base.exists():
            plugins_base.mkdir(parents=True, exist_ok=True)

        # Derive filename from gap_id
        plugin_filename = f"auto_{report.gap_id.lower().replace('-', '')}_{report.zip_stem[:20]}.py"
        plugin_path = plugins_base / plugin_filename

        plugin_path.write_text(code_patch, encoding="utf-8")
        logger.info(f"[ScoutAgent] Promoted plugin to: {plugin_path}")
        return str(plugin_path)

    def _record_evolution(
        self,
        zip_stem: str,
        gap_id: str,
        gap_desc: str,
        target_stage: str,
        target_plugin_interface: str,
        success: bool,
        attempts: int,
        patch_applied: Optional[str] = None,
        promoted_plugin_path: Optional[str] = None,
    ):
        entry = EvolutionLogEntry(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            zip_stem=zip_stem,
            gap_id=gap_id,
            gap_description=gap_desc,
            target_stage=target_stage,
            target_plugin_interface=target_plugin_interface,
            success=success,
            attempts=attempts,
            patch_applied=patch_applied,
            promoted_plugin_path=promoted_plugin_path,
        )

        history: List[Dict[str, Any]] = []
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.append({
            "timestamp": entry.timestamp,
            "zip_stem": entry.zip_stem,
            "gap_id": entry.gap_id,
            "gap_description": entry.gap_description,
            "target_stage": entry.target_stage,
            "target_plugin_interface": entry.target_plugin_interface,
            "success": entry.success,
            "attempts": entry.attempts,
            "patch_applied": entry.patch_applied,
            "promoted_plugin_path": entry.promoted_plugin_path,
        })

        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
