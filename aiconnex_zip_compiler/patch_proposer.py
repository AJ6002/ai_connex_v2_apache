"""
patch_proposer.py — Plugin-Aware Local Ollama LLM Code Patch Proposer (Layer 3)
================================================================================
Generates autonomous BasePlugin subclass code patches for the aiconnex_zip_compiler
plugin pipeline. Targets the specific plugin stage identified by the gap classifier.

Uses active Ollama model `gpt-oss:120b-cloud` (http://localhost:11434). Zero API keys,
zero external overhead.
"""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from pathlib import Path
from typing import Optional

from .reporter import CompilationFailureReport

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are the AIConnex Scout Agent — a specialized File Ingestion Plugin Engineer tasked with evolving the dataset compiler plugin pipeline (aiconnex_zip_compiler/plugins/).

YOUR SINGLE JOB:
Generate an isolated Plugin class that implements the appropriate base class for the target stage, to handle a previously unsupported file format or ingestion pattern.

STRICT BOUNDARIES:
- DO NOT perform data cleaning, missing value imputation, outlier filtering, or feature engineering (handled downstream by ML Pipeline Runner).
- Focus ONLY on unblocking file parsing, directory structure discovery, or multi-table assembly.
- Generate ONLY the plugin class. No CLI scripts, no test files, no other code.

CONTRACT & CONSTRAINTS:
1. Your output MUST be valid, runnable Python code enclosed in a ```python code block.
2. The plugin class MUST inherit from the appropriate base class and use the `@register_plugin` decorator.
3. Required imports:
   ```python
   from pathlib import Path
   from typing import Dict
   import pandas as pd
   from aiconnex_zip_compiler.plugins.base import BaseParserPlugin, MatchResult  # or BaseDiscoveryPlugin, BaseAssemblerPlugin, etc.
   from aiconnex_zip_compiler.plugins.context import PipelineContext
   from aiconnex_zip_compiler.plugins.registry import register_plugin
   ```
4. The class MUST implement:
   - `plugin_id`: str (stable snake_case identifier)
   - `plugin_name`: str (human-readable)
   - `version`: str = "1.0.0"
   - `priority`: int (50 for standard, 70+ for specialized)
   - `probe(self, context: PipelineContext) -> MatchResult`
   - Stage-specific method: `parse()` for parsers, `discover()` for discovery, `assemble()` for assemblers
5. Return ONLY the code block.

STAGE-SPECIFIC TEMPLATES:

For PARSER plugins:
```python
@register_plugin
class CustomFormatParserPlugin(BaseParserPlugin):
    plugin_id = "custom_format_parser"
    plugin_name = "Custom Format Parser Plugin"
    version = "1.0.0"
    priority = 50

    def probe(self, context: PipelineContext) -> MatchResult:
        matching_files = [item for item in context.inventory if item.format_ext == ".custom"]
        if matching_files:
            return MatchResult(supported=True, confidence=0.95, reasons=["Found .custom files"])
        return MatchResult(supported=False, confidence=0.0, reasons=["No .custom files"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        # Read the file and return named DataFrames
        df = pd.read_csv(filepath)  # adapt to actual format
        return {filepath.stem: df}

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            if item.format_ext == ".custom":
                parsed = self.parse(item.filepath, context)
                context.parsed_tables.update(parsed)
        return context
```
"""


class OllamaPatchProposer:
    """
    Plugin-Aware Ollama Patch Proposer targeting active `gpt-oss:120b-cloud` model.
    Generates BasePlugin subclasses for the target stage identified by gap classification.
    """

    def __init__(self, ollama_url: Optional[str] = None, model_name: str = "gpt-oss:120b-cloud"):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = model_name

    def generate_patch(
        self,
        report: CompilationFailureReport,
        sample_file_snippet: str = "",
    ) -> Optional[str]:
        """
        Submits failure report context to local Ollama server.
        Requests a BasePlugin subclass targeting the identified stage.
        """
        stage = getattr(report, "target_stage", "parser")
        interface = getattr(report, "target_plugin_interface", "BaseParserPlugin")

        prompt = f"""
COMPILATION FAILURE REPORT:
- Archive: {report.zip_path}
- Detected Gap ID: {report.gap_id} ({report.gap_description})
- Target Plugin Stage: {stage}
- Target Plugin Interface: {interface}
- Failing Module: {report.failing_module} (Line {report.failing_line})
- Error Message: {report.error_message}

TRACEBACK:
{report.traceback_str}

ARCHIVE TREE STRUCTURE:
{json.dumps([node.relative_path for node in report.archive_tree[:15]], indent=2)}

SAMPLE FILE CONTENT SNIPPET:
{sample_file_snippet[:1000]}

Generate a Python plugin class that inherits from `{interface}` and uses `@register_plugin` decorator.
The plugin must implement `probe()` and the stage-specific method (`parse()` for parsers, `discover()` for discovery, `assemble()` for assemblers).
The plugin should handle the file format or pattern described in the failure report above.
"""

        # Fast direct query to active Ollama model
        for target_model in [self.model_name, "qwen3-coder:480b-cloud", "qwen2.5-coder:7b"]:
            try:
                url = f"{self.ollama_url.rstrip('/')}/api/generate"
                payload = {
                    "model": target_model,
                    "system": SYSTEM_PROMPT,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_ctx": 4096,
                    }
                }

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )

                with urllib.request.urlopen(req, timeout=120) as response:
                    res_body = json.loads(response.read().decode("utf-8"))

                response_text = res_body.get("response", "")
                if response_text:
                    code_patch = self._extract_python_code(response_text)
                    if code_patch:
                        logger.info(f"[OllamaPatchProposer] Generated plugin patch using '{target_model}'")
                        return code_patch
            except Exception as e:
                logger.debug(f"[OllamaPatchProposer] Model '{target_model}' query: {e}")
                continue

        logger.info("[OllamaPatchProposer] Ollama server offline or model not pulled. Falling back to plugin stub.")
        return self._generate_plugin_stub(report)

    def _extract_python_code(self, text: str) -> Optional[str]:
        match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        if "class " in text and "BasePlugin" in text or "register_plugin" in text:
            return text.strip()
        return None

    def _generate_plugin_stub(self, report: CompilationFailureReport) -> str:
        """Generate a heuristic plugin stub when Ollama is offline."""
        stage = getattr(report, "target_stage", "parser")
        interface = getattr(report, "target_plugin_interface", "BaseParserPlugin")
        gap_id_clean = report.gap_id.lower().replace("-", "")
        class_name = f"Auto{gap_id_clean.capitalize()}ParserPlugin"
        plugin_id = f"auto_{gap_id_clean}_{report.zip_stem[:15].lower()}"

        if stage == "parser":
            return f'''"""
Auto-generated parser plugin stub for Gap {report.gap_id} ({report.gap_description})
Generated by AIConnex Scout Agent (heuristic fallback — Ollama offline).
"""

import os
from pathlib import Path
from typing import Dict, List
import pandas as pd

from aiconnex_zip_compiler.plugins.base import BaseParserPlugin, MatchResult
from aiconnex_zip_compiler.plugins.context import PipelineContext
from aiconnex_zip_compiler.plugins.registry import register_plugin


@register_plugin
class {class_name}({interface}):
    plugin_id = "{plugin_id}"
    plugin_name = "Auto-generated plugin for {report.gap_id}"
    version = "1.0.0"
    priority = 50

    def probe(self, context: PipelineContext) -> MatchResult:
        # TODO: Refine detection logic for this specific format
        target_files = [item for item in context.inventory if item.format_ext in [".csv", ".txt"]]
        if target_files:
            return MatchResult(
                supported=True,
                confidence=0.80,
                reasons=["Found potential target files for {report.gap_id}"],
            )
        return MatchResult(supported=False, confidence=0.0, reasons=["No matching files"])

    def parse(self, filepath: Path, context: PipelineContext) -> Dict[str, pd.DataFrame]:
        try:
            df = pd.read_csv(filepath, engine="python", on_bad_lines="skip", encoding_errors="ignore")
            if not df.empty:
                return {{filepath.stem: df}}
        except Exception:
            pass
        return {{}}

    def execute(self, context: PipelineContext) -> PipelineContext:
        for item in context.inventory:
            parsed = self.parse(item.filepath, context)
            context.parsed_tables.update(parsed)
        return context
'''
        else:
            # Generic fallback for non-parser stages
            return f'''"""
Auto-generated {stage} plugin stub for Gap {report.gap_id} ({report.gap_description})
Generated by AIConnex Scout Agent (heuristic fallback — Ollama offline).
"""

from pathlib import Path
from typing import Dict
import pandas as pd

from aiconnex_zip_compiler.plugins.base import BasePlugin, MatchResult
from aiconnex_zip_compiler.plugins.context import PipelineContext
from aiconnex_zip_compiler.plugins.registry import register_plugin


@register_plugin
class Auto{gap_id_clean.capitalize()}Plugin(BasePlugin):
    plugin_id = "{plugin_id}"
    plugin_name = "Auto-generated {stage} plugin for {report.gap_id}"
    version = "1.0.0"
    stage = "{stage}"
    priority = 50

    def probe(self, context: PipelineContext) -> MatchResult:
        return MatchResult(supported=True, confidence=0.70, reasons=["Fallback {stage} plugin"])

    def execute(self, context: PipelineContext) -> PipelineContext:
        return context
'''
