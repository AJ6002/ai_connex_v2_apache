"""
intelligence/problem_discoverer.py - Stage 7: Problem Discovery + Dynamic Intent
===============================================================================
Replaces the hardcoded IntentClassifier if/elif menu entirely.

Given everything learned in Stages 1-6, the LLM decides:
  - what this dataset actually is (free-form domain, not a fixed enum)
  - what logical partitions exist (fault modes, operating conditions, assets)
    and what dimension separates them
  - the QUESTION to ask the field engineer, written in their language
  - the OPTIONS to offer, each carrying the compiler instructions needed to
    execute that choice

Nothing about the question text, the option labels, the partition names, or the
merge strategy is written in advance. All of it is generated per-dataset.

Output modes an option may request:
  single_merged      -> one combined table for one model
  per_partition_batch-> N separate table sets, one model per partition
                        (this is the "individual model per fault mode" case)
  keep_separate      -> emit tables as-is without combining
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient, LLMUnavailableError
from .models import (
    ArchiveTree,
    GeneratedIntentOption,
    PartitionGroup,
    ProblemHypothesis,
    SchemaRoles,
    SemanticLabel,
    TableMetadata,
    TableRelationship,
)
from .validation import dedupe_with_suffix, safe_choice, safe_confidence, stable_slug

logger = logging.getLogger(__name__)

VALID_OUTPUT_MODES = {"single_merged", "per_partition_batch", "keep_separate"}
VALID_MERGE_STRATEGIES = {"key_join", "vertical_stack", "index_align", "none", "auto"}


SYSTEM_PROMPT = """You are a senior ML solutions architect talking to a FIELD ENGINEER, not a data scientist.

You are given a complete analysis of an uploaded dataset: its archive structure,
per-table schemas with inferred column roles, the real-world meaning of columns,
and how the tables relate.

Produce two things:

A) Your understanding of the dataset (domain, purpose, structure, partitions).

B) A single question for the user, plus 2-4 options.

CRITICAL RULES FOR THE QUESTION AND OPTIONS:
- The user does NOT know machine learning. Never use the words: regression,
  classification, feature, target, label, join, merge, schema, dataframe,
  cardinality, training set.
- Ask about the OUTCOME they want in plain operational language, e.g. "predict
  when this equipment will fail", "spot abnormal behaviour", "forecast tomorrow's
  readings", "estimate remaining service life".
- If the dataset contains multiple distinct partitions (different fault modes,
  operating conditions, machines, sites, or time periods), one option MUST offer
  building ONE MODEL PER PARTITION (output_mode "per_partition_batch") and another
  MUST offer ONE COMBINED MODEL across all of them (output_mode "single_merged").
  Describe the operational tradeoff in the description, not the technical one.
- Each option must carry the compiler instructions needed to execute it.

Respond with ONLY a JSON object in exactly this shape:
{
  "domain": "<free-form domain description, e.g. 'gas compressor condition monitoring'>",
  "domain_confidence": 0.9,
  "dataset_purpose": "<why this data was collected, 1-2 sentences>",
  "structural_shape": "<plain description of how the archive/tables are organised>",
  "partition_dimension_name": "<what separates the partitions in plain words, e.g. 'fault mode', 'operating condition', 'machine', or null if none>",
  "detected_partitions": [
    {
      "group_id": "<stable id derived from the data, e.g. FD001>",
      "group_label": "<plain language label for the user>",
      "member_tables": ["<table names belonging to this partition>"],
      "partition_dimension": "<echo partition_dimension_name>"
    }
  ],
  "question_for_user": "<the single question to ask, in field-engineer language>",
  "intent_options": [
    {
      "label": "<short plain-language choice, no ML jargon>",
      "description": "<when to pick this and what they get, operational language>",
      "is_recommended": true,
      "output_mode": "single_merged | per_partition_batch | keep_separate",
      "merge_strategy": "key_join | vertical_stack | index_align | none | auto",
      "tables_to_include": ["<table names, empty list means all>"],
      "tables_to_exclude": ["<table names to leave out, empty list if none>"],
      "partition_by": "<partition_dimension_name if output_mode is per_partition_batch, else null>",
      "target_column": "<existing column name to predict, or null>",
      "target_synthesis": "<if the target must be derived, describe the derivation in one sentence, else null>"
    }
  ],
  "reasoning": "<2-4 sentences explaining your overall interpretation>"
}

Rules:
- Only reference table names and column names that appear in the provided analysis.
- Exactly one option should have is_recommended true.
- detected_partitions may be an empty list if the dataset has no natural partitions.
- All confidence values are floats 0.0-1.0.
- Do NOT include an "option_id" field - the caller assigns stable ids itself."""


class ProblemDiscoverer:
    """LLM-driven problem framing and dynamic HITL option generation."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm = llm_client
        self.llm_model_used: Optional[str] = None
        self.used_llm = False

    def discover(
        self,
        archive_tree: Optional[ArchiveTree],
        table_metadata: List[TableMetadata],
        schema_roles: List[SchemaRoles],
        relationships: List[TableRelationship],
        semantic_labels: List[SemanticLabel],
    ) -> Optional[ProblemHypothesis]:
        """Frame the ML problem and generate the user-facing question + options."""
        if self.llm is None:
            logger.warning("[ProblemDiscoverer] No LLM client - cannot discover problem")
            return None

        if not table_metadata:
            logger.warning("[ProblemDiscoverer] No table metadata - cannot discover problem")
            return None

        payload = self._build_payload(
            archive_tree, table_metadata, schema_roles, relationships, semantic_labels
        )

        user_prompt = (
            "Analyse this dataset and produce the question and options for the user.\n\n"
            + json.dumps(payload, indent=2)
        )

        try:
            response = self.llm.complete_json(SYSTEM_PROMPT, user_prompt, temperature=0.2)
        except LLMUnavailableError as e:
            logger.warning(f"[ProblemDiscoverer] LLM unavailable: {e}")
            return None

        self.used_llm = True
        self.llm_model_used = response.model_used

        return self._parse_hypothesis(response.data, table_metadata)

    # -- Payload -----------------------------------------------------------

    def _build_payload(
        self,
        archive_tree: Optional[ArchiveTree],
        table_metadata: List[TableMetadata],
        schema_roles: List[SchemaRoles],
        relationships: List[TableRelationship],
        semantic_labels: List[SemanticLabel],
    ) -> Dict[str, Any]:
        roles_by_table = {r.table_name: r for r in schema_roles}
        labels_by_table: Dict[str, List[SemanticLabel]] = {}
        for label in semantic_labels:
            labels_by_table.setdefault(label.table_name, []).append(label)

        tables_payload = []
        for table in table_metadata[:40]:
            roles = roles_by_table.get(table.table_name)
            labels = labels_by_table.get(table.table_name, [])

            tables_payload.append(
                {
                    "table_name": table.table_name,
                    "source_path": table.source_path,
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "sampling_interval": table.sampling_interval_guess,
                    "table_role": roles.table_role if roles else "unknown",
                    "grain": roles.grain_description if roles else None,
                    "entity_key_columns": roles.entity_key_columns if roles else [],
                    "time_index_columns": roles.time_index_columns if roles else [],
                    "candidate_target_columns": roles.candidate_target_columns if roles else [],
                    "column_semantics": [
                        {
                            "column": label.column_name,
                            "means": label.semantic_name,
                            "measurement_type": label.measurement_type,
                            "unit": label.unit_guess,
                        }
                        for label in labels[:40]
                    ],
                }
            )

        payload: Dict[str, Any] = {"tables": tables_payload}

        if archive_tree:
            payload["archive"] = {
                "archive_name": archive_tree.archive_name,
                "file_count": len(archive_tree.nodes),
                "max_nesting_depth": archive_tree.max_depth,
                "nested_archive_count": archive_tree.nested_archive_count,
                "directory_layout": archive_tree.directory_layout[:30],
                "example_file_paths": [n.relative_path for n in archive_tree.nodes[:40]],
            }

        if relationships:
            payload["table_relationships"] = [
                {
                    "left_table": r.left_table,
                    "right_table": r.right_table,
                    "relationship_type": r.relationship_type,
                    "join_keys": r.join_keys,
                    "join_strategy": r.join_strategy,
                }
                for r in relationships[:40]
            ]

        return payload

    # -- Response parsing --------------------------------------------------

    def _parse_hypothesis(
        self, data: Dict[str, Any], table_metadata: List[TableMetadata]
    ) -> ProblemHypothesis:
        valid_tables = {t.table_name for t in table_metadata}
        valid_columns = {c.name for t in table_metadata for c in t.columns}

        partitions: List[PartitionGroup] = []
        raw_partitions = data.get("detected_partitions", [])
        if isinstance(raw_partitions, list):
            for item in raw_partitions:
                if not isinstance(item, dict):
                    continue
                members = item.get("member_tables", [])
                members = (
                    [str(m) for m in members if str(m) in valid_tables]
                    if isinstance(members, list)
                    else []
                )
                group_id = str(item.get("group_id", "")).strip()
                if not group_id:
                    continue
                partitions.append(
                    PartitionGroup(
                        group_id=group_id,
                        group_label=str(item.get("group_label", group_id)),
                        member_tables=members,
                        partition_dimension=item.get("partition_dimension"),
                    )
                )

        options: List[GeneratedIntentOption] = []
        seen_ids: set = set()
        raw_options = data.get("intent_options", [])
        if isinstance(raw_options, list):
            for item in raw_options:
                option = self._parse_option(item, valid_tables, valid_columns, seen_ids)
                if option:
                    options.append(option)

        # Guarantee exactly one recommended option
        if options and not any(o.is_recommended for o in options):
            options[0].is_recommended = True
        recommended_seen = False
        for option in options:
            if option.is_recommended:
                if recommended_seen:
                    option.is_recommended = False
                recommended_seen = True

        domain_confidence = safe_confidence(data.get("domain_confidence", 0.0))

        return ProblemHypothesis(
            domain=str(data.get("domain", "unknown")),
            domain_confidence=domain_confidence,
            dataset_purpose=str(data.get("dataset_purpose", "")),
            structural_shape=str(data.get("structural_shape", "")),
            detected_partitions=partitions,
            partition_dimension_name=data.get("partition_dimension_name"),
            question_for_user=str(
                data.get("question_for_user", "What do you want the model to do?")
            ),
            intent_options=options,
            llm_reasoning=data.get("reasoning"),
        )

    def _parse_option(
        self, item: Any, valid_tables: set, valid_columns: set, seen_ids: set
    ) -> Optional[GeneratedIntentOption]:
        if not isinstance(item, dict):
            return None

        label = str(item.get("label", "")).strip()
        if not label:
            return None

        output_mode = safe_choice(
            item.get("output_mode"), VALID_OUTPUT_MODES, default="single_merged"
        )
        merge_strategy = safe_choice(
            item.get("merge_strategy"), VALID_MERGE_STRATEGIES, default="auto"
        )

        def clean_tables(key: str) -> List[str]:
            raw = item.get(key, [])
            if not isinstance(raw, list):
                return []
            return [str(t) for t in raw if str(t) in valid_tables]

        tables_to_include = clean_tables("tables_to_include")
        partition_by = item.get("partition_by")

        target_column = item.get("target_column")
        if target_column is not None:
            target_column = str(target_column)
            if target_column not in valid_columns:
                logger.debug(
                    f"[ProblemDiscoverer] Discarding hallucinated target_column '{target_column}'"
                )
                target_column = None

        # Stable id: derived from STRUCTURAL fields (what the compiler will
        # actually do), never from the LLM's free-text wording. This keeps
        # --strategy <id> and lockfile replay reliable across runs, because
        # the same underlying choice always produces the same id even though
        # the LLM phrases the label/description differently each time.
        raw_id = stable_slug(
            output_mode,
            merge_strategy,
            target_column,
            "_".join(sorted(tables_to_include)) if tables_to_include else None,
        )
        option_id = dedupe_with_suffix(raw_id, seen_ids)

        return GeneratedIntentOption(
            option_id=option_id,
            label=label,
            description=str(item.get("description", "")),
            is_recommended=bool(item.get("is_recommended", False)),
            output_mode=output_mode,
            merge_strategy=merge_strategy,
            tables_to_include=tables_to_include,
            tables_to_exclude=clean_tables("tables_to_exclude"),
            partition_by=partition_by,
            target_column=target_column,
            target_synthesis=item.get("target_synthesis"),
        )
