"""
intelligence/semantic_analyzer.py - Stage 6: Semantic Column Understanding
=========================================================================
Assigns real-world physical/business meaning to columns using LLM domain
knowledge. This is the stage that resolves things a parser fundamentally
cannot, for example:

    PT01  -> Pressure Transmitter 01   (measurement_type: pressure, unit: bar)
    FT01  -> Flow Transmitter 01       (measurement_type: flow,     unit: kg/h)
    TT01  -> Temperature Transmitter 01(measurement_type: temperature, unit: degC)
    s2    -> Total temperature at LPC outlet (C-MAPSS sensor convention)

No abbreviation dictionary is hardcoded. The LLM reasons from the column name
together with the observed value range, dtype, and sample values, which lets it
distinguish (for example) a pressure column reading 0-10 bar from a percentage
column reading 0-100.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient, LLMUnavailableError
from .models import SchemaRoles, SemanticLabel, TableMetadata
from .validation import safe_confidence

logger = logging.getLogger(__name__)

MAX_COLUMNS_PER_CALL = 60


SYSTEM_PROMPT = """You are an industrial instrumentation and data domain expert.

You are given columns from a dataset: their names, statistical profiles (dtype,
value range, mean, std, cardinality, sample values), and the dataset's apparent
domain context. Column names are frequently cryptic industrial tags or
abbreviations.

Your job: determine what each column ACTUALLY MEASURES in the real world.

Use BOTH the name and the observed values. Examples of the reasoning expected:
- A column named "PT01" ranging 0-10 is very likely a Pressure Transmitter in bar,
  whereas ranging 0-100 could be a percentage of full scale - use the range to decide.
- Instrument tag prefixes commonly follow ISA-5.1 conventions: PT=pressure
  transmitter, TT=temperature transmitter, FT=flow transmitter, LT=level
  transmitter, VT=vibration transmitter, AT=analytical transmitter.
- Domain-specific sensor numbering schemes (for example turbofan engine sensor
  suites) have documented physical meanings - state them when you recognise the
  convention.
- A monotonic integer column with a name like "cycle" or "t" is an operating-time
  counter, not a physical measurement.

Respond with ONLY a JSON object in exactly this shape:
{
  "labels": [
    {
      "table_name": "<echo exactly>",
      "column_name": "<echo exactly>",
      "semantic_name": "<human readable meaning, e.g. 'Pressure Transmitter 01 - compressor suction'>",
      "measurement_type": "pressure | temperature | flow | level | vibration | speed | current | voltage | power | position | time | identifier | count | ratio | label | unknown",
      "unit_guess": "<physical unit, e.g. bar, degC, kg/h, mm/s, rpm, A, V, kW, or null>",
      "equipment_context": "<what equipment/subsystem it belongs to, or null>",
      "confidence": 0.85,
      "reasoning": "<one sentence citing the name convention and/or value range>"
    }
  ]
}

Rules:
- Echo table_name and column_name EXACTLY as provided. Never rename or invent columns.
- Use measurement_type "unknown" only when you genuinely cannot infer it.
- unit_guess must be a physical unit string or null - never a description.
- Provide one entry for every column given.
- confidence is a float 0.0-1.0. Be honest: lower it when the name is opaque and
  the value range is ambiguous."""


class SemanticAnalyzer:
    """LLM-driven physical meaning assignment for columns."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client
        self.llm_model_used: Optional[str] = None
        self.used_llm = False

    def analyze(
        self,
        table_metadata: List[TableMetadata],
        schema_roles: Optional[List[SchemaRoles]] = None,
        domain_hint: Optional[str] = None,
    ) -> List[SemanticLabel]:
        """
        Assign semantic meaning to columns across all tables.

        Batches columns across multiple LLM calls when a dataset is wide, so
        very wide tables do not overflow the context window.
        """
        if self.llm is None:
            logger.warning("[SemanticAnalyzer] No LLM client - skipping semantic analysis")
            return []

        if not table_metadata:
            return []

        roles_by_table = {r.table_name: r for r in (schema_roles or [])}
        batches = self._build_batches(table_metadata, roles_by_table)

        labels: List[SemanticLabel] = []
        for batch_index, batch in enumerate(batches, 1):
            logger.info(
                f"[SemanticAnalyzer] Semantic batch {batch_index}/{len(batches)} "
                f"({len(batch['columns'])} columns)"
            )
            labels.extend(self._analyze_batch(batch, domain_hint, table_metadata))

        return labels

    # -- Batching ----------------------------------------------------------

    def _build_batches(
        self,
        table_metadata: List[TableMetadata],
        roles_by_table: Dict[str, SchemaRoles],
    ) -> List[Dict[str, Any]]:
        """
        Group columns into LLM-sized batches.

        Constant columns and pure identifiers are still included, because knowing
        that a constant column is (for example) a plant ID is useful context, but
        they are cheap to describe so they do not dominate a batch.
        """
        batches: List[Dict[str, Any]] = []
        current: List[Dict[str, Any]] = []

        for table in table_metadata:
            roles = roles_by_table.get(table.table_name)
            for column in table.columns:
                current.append(
                    {
                        "table_name": table.table_name,
                        "column_name": column.name,
                        "dtype": column.inferred_dtype,
                        "min": column.min_value,
                        "max": column.max_value,
                        "mean": column.mean_value,
                        "std": column.std_value,
                        "unique_count": column.unique_count,
                        "cardinality_ratio": column.cardinality_ratio,
                        "is_constant": column.is_constant,
                        "is_monotonic_increasing": column.is_monotonic_increasing,
                        "structural_role": self._role_of(column.name, roles),
                        "samples": column.sample_values[:3],
                    }
                )

                if len(current) >= MAX_COLUMNS_PER_CALL:
                    batches.append({"columns": current})
                    current = []

        if current:
            batches.append({"columns": current})

        return batches

    @staticmethod
    def _role_of(column_name: str, roles: Optional[SchemaRoles]) -> str:
        """Report the Stage 5 structural role as context for semantic reasoning."""
        if roles is None:
            return "unknown"
        if column_name in roles.entity_key_columns:
            return "entity_key"
        if column_name in roles.time_index_columns:
            return "time_index"
        if column_name in roles.candidate_target_columns:
            return "candidate_target"
        if column_name in roles.metadata_columns:
            return "metadata"
        if column_name in roles.feature_columns:
            return "feature"
        return "unknown"

    # -- Single batch call -------------------------------------------------

    def _analyze_batch(
        self,
        batch: Dict[str, Any],
        domain_hint: Optional[str],
        table_metadata: List[TableMetadata],
    ) -> List[SemanticLabel]:
        payload: Dict[str, Any] = {"columns": batch["columns"]}
        if domain_hint:
            payload["domain_context"] = domain_hint

        user_prompt = (
            "Determine what each of these columns measures in the real world.\n\n"
            + json.dumps(payload, indent=2)
        )

        try:
            response = self.llm.complete_json(SYSTEM_PROMPT, user_prompt)
        except LLMUnavailableError as e:
            logger.warning(f"[SemanticAnalyzer] LLM unavailable for semantic batch: {e}")
            return []

        self.used_llm = True
        self.llm_model_used = response.model_used

        raw_labels = response.data.get("labels", [])
        if not isinstance(raw_labels, list):
            logger.warning("[SemanticAnalyzer] LLM returned unexpected shape for 'labels'")
            return []

        # Validate against the real (table, column) pairs we asked about
        requested = {(c["table_name"], c["column_name"]) for c in batch["columns"]}

        results: List[SemanticLabel] = []
        for item in raw_labels:
            if not isinstance(item, dict):
                continue

            table_name = str(item.get("table_name", ""))
            column_name = str(item.get("column_name", ""))
            if (table_name, column_name) not in requested:
                logger.debug(
                    f"[SemanticAnalyzer] Discarding label for unrequested column "
                    f"{table_name}.{column_name}"
                )
                continue

            confidence = safe_confidence(item.get("confidence"))

            unit = item.get("unit_guess")
            results.append(
                SemanticLabel(
                    table_name=table_name,
                    column_name=column_name,
                    semantic_name=str(item.get("semantic_name", column_name)),
                    measurement_type=item.get("measurement_type"),
                    unit_guess=str(unit) if unit else None,
                    equipment_context=item.get("equipment_context"),
                    confidence=confidence,
                    llm_reasoning=item.get("reasoning"),
                )
            )

        return results
