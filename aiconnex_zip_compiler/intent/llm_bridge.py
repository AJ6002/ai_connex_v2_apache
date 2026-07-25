"""
intent/llm_bridge.py - Adapter: Intelligence Report -> Intent Layer Types
=========================================================================
Converts LLM-generated intelligence output into the dataclasses the existing
terminal prompter and compiler already understand:

  ProblemHypothesis      -> DatasetCard        (what gets displayed)
  GeneratedIntentOption  -> IntentOption       (what gets offered)
  GeneratedIntentOption  -> CompilationStrategy(what the compiler executes)

This keeps the TUI and plugin pipeline decoupled from the intelligence layer:
if the LLM is unavailable, the compiler falls back to the legacy heuristic
CardGenerator/IntentClassifier path and these adapters are simply not used.

No dataset knowledge lives here - this is pure structural translation.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..intelligence.models import (
    GeneratedIntentOption,
    IntelligenceReport,
    ProblemHypothesis,
)
from .models import CompilationStrategy, DatasetCard, IntentOption

logger = logging.getLogger(__name__)


# Maps the LLM's declared merge_strategy to the compiler's internal merge_rule
# and the assembler plugin that implements it.
_MERGE_STRATEGY_MAP: Dict[str, tuple] = {
    # llm merge_strategy: (compiler merge_rule, assembler_policy_override)
    "vertical_stack": ("vertical_stack", "vertical_stack_assembler"),
    "key_join": ("merge_on_key", "relational_join_assembler"),
    "index_align": ("merge_on_key", "relational_join_assembler"),
    "none": ("keep_separate", "relational_join_assembler"),
    "auto": ("default", None),
}


def report_to_dataset_card(report: IntelligenceReport) -> Optional[DatasetCard]:
    """
    Build the DatasetCard the terminal prompter displays, from LLM findings.

    Everything shown to the user (domain, structure summary) comes from LLM
    reasoning rather than regex domain matching.
    """
    hypothesis = report.problem_hypothesis
    if hypothesis is None:
        return None

    # Collect entity/time keys discovered by the schema analyzer across all tables
    entity_keys: List[str] = []
    time_keys: List[str] = []
    for roles in report.schema_roles:
        for column in roles.entity_key_columns:
            if column not in entity_keys:
                entity_keys.append(column)
        for column in roles.time_index_columns:
            if column not in time_keys:
                time_keys.append(column)

    # Feature columns, labelled with their semantic meaning where known
    semantic_by_column = {
        label.column_name: label.semantic_name for label in report.semantic_labels
    }
    sensor_columns: List[str] = []
    for roles in report.schema_roles:
        for column in roles.feature_columns:
            display = semantic_by_column.get(column, column)
            if display not in sensor_columns:
                sensor_columns.append(display)

    partition_ids = [p.group_id for p in hypothesis.detected_partitions]

    total_rows = sum(t.row_count for t in report.table_metadata)
    file_count = len(report.archive_tree.nodes) if report.archive_tree else 0

    summary = hypothesis.structural_shape or hypothesis.dataset_purpose or hypothesis.domain

    return DatasetCard(
        dataset_name=report.archive_name,
        domain=hypothesis.domain,
        dataset_type=_infer_dataset_type_label(hypothesis),
        entity_keys=entity_keys,
        time_keys=time_keys,
        sensor_columns=sensor_columns,
        detected_conditions=partition_ids,
        detected_sheets=[t.table_name for t in report.table_metadata],
        file_count=file_count,
        total_rows_estimate=total_rows,
        summary=summary,
    )


def report_to_intent_options(report: IntelligenceReport) -> List[IntentOption]:
    """Convert LLM-generated options into prompter-displayable IntentOptions."""
    hypothesis = report.problem_hypothesis
    if hypothesis is None or not hypothesis.intent_options:
        return []

    options: List[IntentOption] = []
    for generated in hypothesis.intent_options:
        options.append(
            IntentOption(
                option_id=generated.option_id,
                label=generated.label,
                description=generated.description,
                is_default=generated.is_recommended,
                output_mode=generated.output_mode,
            )
        )
    return options


def resolve_llm_strategy(
    choice_id: str,
    report: IntelligenceReport,
) -> Optional[CompilationStrategy]:
    """
    Build the CompilationStrategy for a chosen LLM-generated option.

    Returns None if the choice_id does not correspond to any generated option,
    letting the caller fall back to the legacy resolver.
    """
    hypothesis = report.problem_hypothesis
    if hypothesis is None:
        return None

    generated = next(
        (o for o in hypothesis.intent_options if o.option_id == choice_id), None
    )
    if generated is None:
        return None

    merge_rule, assembler_override = _MERGE_STRATEGY_MAP.get(
        generated.merge_strategy, ("default", None)
    )

    # per_partition_batch always emits separate artifact sets, so the assembler
    # must not collapse tables together across partitions.
    if generated.output_mode == "per_partition_batch":
        merge_rule = "keep_separate" if generated.merge_strategy in ("none", "auto") else merge_rule

    partitions = [
        {
            "group_id": p.group_id,
            "group_label": p.group_label,
            "member_tables": p.member_tables,
        }
        for p in hypothesis.detected_partitions
    ]

    scope = {
        "single_merged": "unified",
        "per_partition_batch": "per_condition",
        "keep_separate": "all",
    }.get(generated.output_mode, "all")

    strategy = CompilationStrategy(
        intent_id=generated.option_id,
        scope=scope,
        condition_filter=None,
        sheets_to_include=list(generated.tables_to_include),
        sheets_to_exclude=list(generated.tables_to_exclude),
        merge_rule=merge_rule,
        target_synthesis=generated.target_synthesis or "auto",
        target_column_hint=generated.target_column,
        assembler_policy_override=assembler_override,
        output_mode=generated.output_mode,
        partition_by=generated.partition_by or hypothesis.partition_dimension_name,
        partitions=partitions if generated.output_mode == "per_partition_batch" else [],
        generated_by_llm=True,
    )

    logger.info(
        f"[LLMBridge] Resolved '{choice_id}' -> output_mode={strategy.output_mode}, "
        f"merge_rule={strategy.merge_rule}, partitions={len(strategy.partitions)}"
    )
    return strategy


def _infer_dataset_type_label(hypothesis: ProblemHypothesis) -> str:
    """
    Produce a short structural label for the DatasetCard.

    This is presentation only - it does not drive any routing decision (unlike
    the legacy CardGenerator._classify_type, whose output fed a hardcoded
    if/elif menu). Routing comes from the LLM's own option instructions.
    """
    if hypothesis.detected_partitions:
        dimension = hypothesis.partition_dimension_name or "partition"
        return f"partitioned_by_{dimension.replace(' ', '_').lower()}"
    return "single_population"
