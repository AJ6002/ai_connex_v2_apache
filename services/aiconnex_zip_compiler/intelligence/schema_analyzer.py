"""
intelligence/schema_analyzer.py - Stage 5: Schema Role Discovery
================================================================
Infers the STRUCTURAL role of every column and the relationships between
tables, using LLM reasoning over the statistical evidence from Stage 4.

Deliberately NOT name-based. The LLM is given cardinality ratios, monotonicity,
missing percentages, value ranges, and sample values so it can conclude
"this is the entity key" from behaviour (low cardinality, repeats across rows)
rather than from a column happening to be called `unit_id`.

That means a dataset with columns named X1, X2, Y still gets correct role
assignment, which regex-based detection could never do.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

try:
    from .llm_client import LLMClient, LLMUnavailableError
except ImportError:
    class LLMUnavailableError(Exception): pass
    LLMClient = None

from .models import SchemaRoles, TableMetadata, TableRelationship
from .validation import safe_confidence

logger = logging.getLogger(__name__)


ROLES_SYSTEM_PROMPT = """You are a data schema analyst. You infer the structural role of each column from its STATISTICAL BEHAVIOUR, not from its name.

You receive statistical profiles of tables. For each column you get: inferred dtype,
missing percentage, unique count, cardinality ratio (unique/non-null), whether it is
constant, whether it is monotonically increasing, min/max/mean/std, and sample values.

Key reasoning signals:
- An ENTITY KEY repeats across many rows: low cardinality_ratio, integer or short
  categorical, not monotonic overall, no missing values.
- A TIME INDEX is monotonic increasing (globally or within each entity), datetime or
  an integer counter/cycle, evenly spaced.
- A TARGET is often monotonic within an entity group (countdown/degradation), or a
  label column with few distinct values, or an outcome measure. It may also be absent
  entirely and need deriving.
- FEATURES are continuous measurements with wide value ranges and high cardinality.
- METADATA columns are constant or near-constant across the whole table.
- Columns that are entirely constant carry no modelling signal.

Respond with ONLY a JSON object in exactly this shape:
{
  "tables": [
    {
      "table_name": "<echo exactly>",
      "table_role": "fact | dimension | snapshot | metadata | ground_truth",
      "grain_description": "<what one row represents, e.g. 'one row per engine per cycle'>",
      "entity_key_columns": ["<column names>"],
      "time_index_columns": ["<column names>"],
      "candidate_target_columns": ["<column names, may be empty>"],
      "feature_columns": ["<column names>"],
      "metadata_columns": ["<column names>"],
      "confidence": 0.9,
      "reasoning": "<2-3 sentences citing the statistics that drove your decision>"
    }
  ]
}

Rules:
- Every column of a table must appear in exactly one of the role lists.
- Echo column names EXACTLY as provided. Never rename or invent columns.
- candidate_target_columns may be empty if no column is a plausible target.
- confidence is a float 0.0-1.0."""


RELATIONSHIPS_SYSTEM_PROMPT = """You are a relational data architect determining how multiple tables relate.

You receive per-table schemas with their inferred roles and column statistics.
Determine, for each meaningful PAIR of tables, how they relate and how they should
be combined.

relationship_type options:
- "same_schema_partition": tables share (nearly) identical columns and represent
  different slices of the same measurement population (e.g. different operating
  conditions, different months, different assets). Combine with vertical_stack.
- "one_to_many": a dimension/lookup table joins onto a larger fact table on a key.
- "one_to_one": row-aligned parallel channels of the same observations.
- "ground_truth_link": one table holds labels/targets for entities in another.
- "unrelated": no meaningful join.

join_strategy options: "key_join", "index_align", "vertical_stack", "none"

Respond with ONLY a JSON object in exactly this shape:
{
  "relationships": [
    {
      "left_table": "<echo exactly>",
      "right_table": "<echo exactly>",
      "relationship_type": "same_schema_partition",
      "join_keys": ["<shared column names, empty for vertical_stack or index_align>"],
      "join_strategy": "vertical_stack",
      "confidence": 0.9,
      "reasoning": "<one or two sentences>"
    }
  ]
}

Rules:
- Only reference table names that were provided. Never invent tables.
- join_keys must be columns that genuinely exist in BOTH tables.
- If there is exactly one table, return an empty relationships list.
- Do not enumerate every pair when many tables share one schema; it is enough to
  report the representative pairings that establish the pattern.
- confidence is a float 0.0-1.0."""


class SchemaAnalyzer:
    """LLM-driven structural role and relationship inference."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client
        self.llm_model_used: Optional[str] = None
        self.used_llm = False

    def analyze(
        self, table_metadata: List[TableMetadata]
    ) -> tuple[List[SchemaRoles], List[TableRelationship]]:
        """Infer column roles per table and relationships between tables."""
        if not table_metadata:
            return [], []

        roles = self._infer_roles(table_metadata)
        relationships = self._infer_relationships(table_metadata, roles)
        return roles, relationships

    # -- Roles -------------------------------------------------------------

    def _infer_roles(self, table_metadata: List[TableMetadata]) -> List[SchemaRoles]:
        if self.llm is None:
            logger.warning("[SchemaAnalyzer] No LLM client - skipping role inference")
            return []

        payload = {"tables": [self._compact_table(t) for t in table_metadata[:40]]}
        user_prompt = (
            "Infer the structural role of every column in these tables.\n\n"
            + json.dumps(payload, indent=2)
        )

        try:
            response = self.llm.complete_json(ROLES_SYSTEM_PROMPT, user_prompt)
        except LLMUnavailableError as e:
            logger.warning(f"[SchemaAnalyzer] LLM unavailable for role inference: {e}")
            return []

        self.used_llm = True
        self.llm_model_used = response.model_used

        raw_tables = response.data.get("tables", [])
        if not isinstance(raw_tables, list):
            logger.warning("[SchemaAnalyzer] LLM returned unexpected shape for 'tables'")
            return []

        # Index real column names per table so we can reject hallucinations
        real_columns: Dict[str, set] = {
            t.table_name: {c.name for c in t.columns} for t in table_metadata
        }

        results: List[SchemaRoles] = []
        for item in raw_tables:
            if not isinstance(item, dict):
                continue
            table_name = str(item.get("table_name", ""))
            if table_name not in real_columns:
                logger.warning(f"[SchemaAnalyzer] LLM referenced unknown table '{table_name}'")
                continue

            valid = real_columns[table_name]

            def clean(key: str) -> List[str]:
                raw = item.get(key, [])
                if not isinstance(raw, list):
                    return []
                return [str(c) for c in raw if str(c) in valid]

            confidence = safe_confidence(item.get("confidence"))

            results.append(
                SchemaRoles(
                    table_name=table_name,
                    entity_key_columns=clean("entity_key_columns"),
                    time_index_columns=clean("time_index_columns"),
                    candidate_target_columns=clean("candidate_target_columns"),
                    feature_columns=clean("feature_columns"),
                    metadata_columns=clean("metadata_columns"),
                    table_role=str(item.get("table_role", "unknown")),
                    grain_description=item.get("grain_description"),
                    confidence=confidence,
                    llm_reasoning=item.get("reasoning"),
                )
            )

        return results

    # -- Relationships -----------------------------------------------------

    def _infer_relationships(
        self, table_metadata: List[TableMetadata], roles: List[SchemaRoles]
    ) -> List[TableRelationship]:
        if self.llm is None or len(table_metadata) < 2:
            return []

        roles_by_table = {r.table_name: r for r in roles}
        payload = {
            "tables": [
                {
                    "table_name": t.table_name,
                    "row_count": t.row_count,
                    "columns": [c.name for c in t.columns],
                    "table_role": roles_by_table.get(t.table_name).table_role
                    if roles_by_table.get(t.table_name)
                    else "unknown",
                    "entity_key_columns": roles_by_table.get(t.table_name).entity_key_columns
                    if roles_by_table.get(t.table_name)
                    else [],
                }
                for t in table_metadata[:40]
            ]
        }

        user_prompt = (
            "Determine how these tables relate and how they should be combined.\n\n"
            + json.dumps(payload, indent=2)
        )

        try:
            response = self.llm.complete_json(RELATIONSHIPS_SYSTEM_PROMPT, user_prompt)
        except LLMUnavailableError as e:
            logger.warning(f"[SchemaAnalyzer] LLM unavailable for relationship inference: {e}")
            return []

        self.used_llm = True
        self.llm_model_used = response.model_used

        raw_rels = response.data.get("relationships", [])
        if not isinstance(raw_rels, list):
            return []

        columns_by_table = {t.table_name: {c.name for c in t.columns} for t in table_metadata}
        valid_tables = set(columns_by_table.keys())

        results: List[TableRelationship] = []
        for item in raw_rels:
            if not isinstance(item, dict):
                continue
            left = str(item.get("left_table", ""))
            right = str(item.get("right_table", ""))
            if left not in valid_tables or right not in valid_tables or left == right:
                continue

            raw_keys = item.get("join_keys", [])
            join_keys = []
            if isinstance(raw_keys, list):
                shared = columns_by_table[left] & columns_by_table[right]
                join_keys = [str(k) for k in raw_keys if str(k) in shared]

            confidence = safe_confidence(item.get("confidence"))

            results.append(
                TableRelationship(
                    left_table=left,
                    right_table=right,
                    relationship_type=str(item.get("relationship_type", "unrelated")),
                    join_keys=join_keys,
                    join_strategy=str(item.get("join_strategy", "none")),
                    confidence=confidence,
                    llm_reasoning=item.get("reasoning"),
                )
            )

        return results

    # -- Payload shaping ---------------------------------------------------

    @staticmethod
    def _compact_table(table: TableMetadata) -> Dict[str, Any]:
        """Trim a TableMetadata into a token-efficient LLM payload."""
        return {
            "table_name": table.table_name,
            "row_count": table.row_count,
            "column_count": table.column_count,
            "sampling_interval": table.sampling_interval_guess,
            "duplicate_row_count": table.duplicate_row_count,
            "columns": [
                {
                    "name": c.name,
                    "dtype": c.inferred_dtype,
                    "missing_pct": c.missing_pct,
                    "unique_count": c.unique_count,
                    "cardinality_ratio": c.cardinality_ratio,
                    "is_constant": c.is_constant,
                    "is_monotonic_increasing": c.is_monotonic_increasing,
                    "min": c.min_value,
                    "max": c.max_value,
                    "mean": c.mean_value,
                    "std": c.std_value,
                    "samples": c.sample_values[:3],
                }
                for c in table.columns[:120]
            ],
        }
