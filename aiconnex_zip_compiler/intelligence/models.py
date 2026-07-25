"""
intelligence/models.py - Data Models for the LLM-Driven Intelligence Layer
===========================================================================
Dataclasses for every analysis stage output. Nothing in here encodes
dataset-specific knowledge - all semantic content is filled in at runtime by
LLM reasoning, not by hardcoded lookup tables.

Stage map:
  1. Archive Exploration   -> ArchiveNode, ArchiveTree
  2. Format Detection      -> FileFingerprint
  3. Parser Selection      -> ParserDecision
  4. Metadata Extraction   -> ColumnProfile, TableMetadata
  5. Schema Discovery      -> SchemaRoles, TableRelationship
  6. Semantic Analysis     -> SemanticLabel
  7. Problem Discovery     -> ProblemHypothesis, GeneratedIntentOption
  All                      -> IntelligenceReport
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Stage 1: Archive Exploration
# ---------------------------------------------------------------------------

@dataclass
class ArchiveNode:
    """One file discovered inside the archive (post recursive extraction)."""

    absolute_path: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    depth: int  # nesting depth from archive root
    parent_archive: Optional[str] = None  # set when extracted from a nested archive

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "filename": self.filename,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "depth": self.depth,
            "parent_archive": self.parent_archive,
        }


@dataclass
class ArchiveTree:
    """Complete recursive inventory of the uploaded archive."""

    archive_name: str
    root_path: str
    nodes: List[ArchiveNode] = field(default_factory=list)
    max_depth: int = 0
    nested_archive_count: int = 0
    total_size_bytes: int = 0
    directory_layout: List[str] = field(default_factory=list)  # unique parent dirs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archive_name": self.archive_name,
            "file_count": len(self.nodes),
            "max_depth": self.max_depth,
            "nested_archive_count": self.nested_archive_count,
            "total_size_bytes": self.total_size_bytes,
            "directory_layout": self.directory_layout[:50],
            "nodes": [n.to_dict() for n in self.nodes[:200]],
        }


# ---------------------------------------------------------------------------
# Stage 2: Format Detection
# ---------------------------------------------------------------------------

@dataclass
class FileFingerprint:
    """Detected true format of a file, independent of its extension."""

    relative_path: str
    extension: str
    magic_bytes_hex: str  # first N bytes, hex encoded
    detected_format: str  # e.g. "csv", "matlab_v5", "hdf5", "parquet", "unknown_binary"
    detection_method: str  # "magic_bytes" | "extension" | "text_heuristic" | "llm"
    confidence: float
    is_text: bool = False
    is_binary: bool = False
    encoding_guess: Optional[str] = None
    llm_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "extension": self.extension,
            "magic_bytes_hex": self.magic_bytes_hex,
            "detected_format": self.detected_format,
            "detection_method": self.detection_method,
            "confidence": self.confidence,
            "is_text": self.is_text,
            "is_binary": self.is_binary,
            "encoding_guess": self.encoding_guess,
            "llm_reasoning": self.llm_reasoning,
        }


# ---------------------------------------------------------------------------
# Stage 3: Parser Selection
# ---------------------------------------------------------------------------

@dataclass
class ParserDecision:
    """LLM decision on how to parse a given detected format."""

    detected_format: str
    affected_paths: List[str] = field(default_factory=list)
    chosen_plugin_id: Optional[str] = None  # existing plugin that can handle it
    requires_new_plugin: bool = False
    proposed_plugin_stage: Optional[str] = None  # "parser" | "discovery" | ...
    proposed_approach: Optional[str] = None  # free-text strategy for Scout Agent
    fallback_chain: List[str] = field(default_factory=list)  # e.g. ["numpy.fromfile", "struct"]
    confidence: float = 0.0
    llm_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_format": self.detected_format,
            "affected_paths": self.affected_paths[:20],
            "chosen_plugin_id": self.chosen_plugin_id,
            "requires_new_plugin": self.requires_new_plugin,
            "proposed_plugin_stage": self.proposed_plugin_stage,
            "proposed_approach": self.proposed_approach,
            "fallback_chain": self.fallback_chain,
            "confidence": self.confidence,
            "llm_reasoning": self.llm_reasoning,
        }


# ---------------------------------------------------------------------------
# Stage 4: Metadata Extraction
# ---------------------------------------------------------------------------

@dataclass
class ColumnProfile:
    """Computed statistical profile of a single column. Fully deterministic."""

    name: str
    position: int
    inferred_dtype: str  # "numeric_int" | "numeric_float" | "datetime" | "categorical" | "text" | "boolean" | "empty"
    non_null_count: int = 0
    null_count: int = 0
    missing_pct: float = 0.0
    unique_count: int = 0
    cardinality_ratio: float = 0.0  # unique / non_null
    is_constant: bool = False
    is_monotonic_increasing: bool = False
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    sample_values: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "position": self.position,
            "inferred_dtype": self.inferred_dtype,
            "non_null_count": self.non_null_count,
            "null_count": self.null_count,
            "missing_pct": self.missing_pct,
            "unique_count": self.unique_count,
            "cardinality_ratio": self.cardinality_ratio,
            "is_constant": self.is_constant,
            "is_monotonic_increasing": self.is_monotonic_increasing,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean_value": self.mean_value,
            "std_value": self.std_value,
            "sample_values": self.sample_values[:5],
        }


@dataclass
class TableMetadata:
    """Profile of one parsed logical table."""

    table_name: str
    source_path: str
    row_count: int = 0
    column_count: int = 0
    columns: List[ColumnProfile] = field(default_factory=list)
    sampling_interval_guess: Optional[str] = None  # computed from datetime deltas
    duplicate_row_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "source_path": self.source_path,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "sampling_interval_guess": self.sampling_interval_guess,
            "duplicate_row_count": self.duplicate_row_count,
            "columns": [c.to_dict() for c in self.columns],
        }


# ---------------------------------------------------------------------------
# Stage 6: Semantic Analysis
# ---------------------------------------------------------------------------

@dataclass
class SemanticLabel:
    """LLM-assigned physical/business meaning of a column."""

    table_name: str
    column_name: str
    semantic_name: str  # e.g. "Pressure Transmitter 01"
    measurement_type: Optional[str] = None  # "pressure" | "temperature" | "flow" | "vibration" | ...
    unit_guess: Optional[str] = None  # "bar" | "degC" | "kg/h" | ...
    equipment_context: Optional[str] = None  # "compressor suction line"
    confidence: float = 0.0
    llm_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "column_name": self.column_name,
            "semantic_name": self.semantic_name,
            "measurement_type": self.measurement_type,
            "unit_guess": self.unit_guess,
            "equipment_context": self.equipment_context,
            "confidence": self.confidence,
            "llm_reasoning": self.llm_reasoning,
        }


# ---------------------------------------------------------------------------
# Stage 5: Schema Discovery
# ---------------------------------------------------------------------------

@dataclass
class TableRelationship:
    """LLM-inferred relationship between two tables."""

    left_table: str
    right_table: str
    relationship_type: str  # "one_to_many" | "one_to_one" | "same_schema_partition" | "unrelated"
    join_keys: List[str] = field(default_factory=list)
    join_strategy: str = "none"  # "key_join" | "index_align" | "vertical_stack" | "none"
    confidence: float = 0.0
    llm_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "left_table": self.left_table,
            "right_table": self.right_table,
            "relationship_type": self.relationship_type,
            "join_keys": self.join_keys,
            "join_strategy": self.join_strategy,
            "confidence": self.confidence,
            "llm_reasoning": self.llm_reasoning,
        }


@dataclass
class SchemaRoles:
    """LLM-inferred structural role assignment for one table."""

    table_name: str
    entity_key_columns: List[str] = field(default_factory=list)
    time_index_columns: List[str] = field(default_factory=list)
    candidate_target_columns: List[str] = field(default_factory=list)
    feature_columns: List[str] = field(default_factory=list)
    metadata_columns: List[str] = field(default_factory=list)
    table_role: str = "unknown"  # "fact" | "dimension" | "snapshot" | "metadata" | "ground_truth"
    grain_description: Optional[str] = None  # "one row per engine per cycle"
    confidence: float = 0.0
    llm_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "entity_key_columns": self.entity_key_columns,
            "time_index_columns": self.time_index_columns,
            "candidate_target_columns": self.candidate_target_columns,
            "feature_columns": self.feature_columns,
            "metadata_columns": self.metadata_columns,
            "table_role": self.table_role,
            "grain_description": self.grain_description,
            "confidence": self.confidence,
            "llm_reasoning": self.llm_reasoning,
        }


# ---------------------------------------------------------------------------
# Stage 7: Problem Discovery + Dynamic Intent Options
# ---------------------------------------------------------------------------

@dataclass
class PartitionGroup:
    """A discovered logical partition (fault mode, operating condition, asset...)."""

    group_id: str  # LLM-derived, e.g. "FD001" or "bearing_1_1"
    group_label: str  # human readable, LLM-generated
    member_tables: List[str] = field(default_factory=list)
    partition_dimension: Optional[str] = None  # what distinguishes it, e.g. "operating condition"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "group_label": self.group_label,
            "member_tables": self.member_tables,
            "partition_dimension": self.partition_dimension,
        }


@dataclass
class GeneratedIntentOption:
    """An LLM-generated choice presented to the user. NOT from a hardcoded menu."""

    option_id: str  # LLM-generated stable snake_case id
    label: str  # plain language, field-engineer readable
    description: str  # why/when to pick this
    is_recommended: bool = False

    # Compiler instructions the LLM attached to this choice
    output_mode: str = "single_merged"  # "single_merged" | "per_partition_batch" | "keep_separate"
    merge_strategy: str = "auto"  # "key_join" | "vertical_stack" | "index_align" | "none" | "auto"
    tables_to_include: List[str] = field(default_factory=list)
    tables_to_exclude: List[str] = field(default_factory=list)
    partition_by: Optional[str] = None  # partition dimension for per_partition_batch mode
    target_column: Optional[str] = None
    target_synthesis: Optional[str] = None  # LLM-described derivation if target must be computed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "label": self.label,
            "description": self.description,
            "is_recommended": self.is_recommended,
            "output_mode": self.output_mode,
            "merge_strategy": self.merge_strategy,
            "tables_to_include": self.tables_to_include,
            "tables_to_exclude": self.tables_to_exclude,
            "partition_by": self.partition_by,
            "target_column": self.target_column,
            "target_synthesis": self.target_synthesis,
        }


@dataclass
class ProblemHypothesis:
    """LLM's understanding of what this dataset is and what can be modeled."""

    domain: str  # LLM-generated, free-form (not from a fixed enum)
    domain_confidence: float = 0.0
    dataset_purpose: str = ""  # what this data was collected for
    structural_shape: str = ""  # LLM-described archive/table shape
    detected_partitions: List[PartitionGroup] = field(default_factory=list)
    partition_dimension_name: Optional[str] = None  # e.g. "fault mode", "operating condition"
    question_for_user: str = ""  # LLM-generated question text
    intent_options: List[GeneratedIntentOption] = field(default_factory=list)
    llm_reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "domain_confidence": self.domain_confidence,
            "dataset_purpose": self.dataset_purpose,
            "structural_shape": self.structural_shape,
            "detected_partitions": [p.to_dict() for p in self.detected_partitions],
            "partition_dimension_name": self.partition_dimension_name,
            "question_for_user": self.question_for_user,
            "intent_options": [o.to_dict() for o in self.intent_options],
            "llm_reasoning": self.llm_reasoning,
        }


# ---------------------------------------------------------------------------
# Aggregate Report
# ---------------------------------------------------------------------------

@dataclass
class StageStatus:
    """Execution record for one intelligence stage."""

    stage_name: str
    succeeded: bool
    used_llm: bool = False
    llm_model: Optional[str] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "succeeded": self.succeeded,
            "used_llm": self.used_llm,
            "llm_model": self.llm_model,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


@dataclass
class IntelligenceReport:
    """
    Complete output of the intelligence layer, written to
    archive_intelligence_report.json in the output directory.
    """

    archive_name: str
    generated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    archive_tree: Optional[ArchiveTree] = None
    fingerprints: List[FileFingerprint] = field(default_factory=list)
    parser_decisions: List[ParserDecision] = field(default_factory=list)
    table_metadata: List[TableMetadata] = field(default_factory=list)
    schema_roles: List[SchemaRoles] = field(default_factory=list)
    relationships: List[TableRelationship] = field(default_factory=list)
    semantic_labels: List[SemanticLabel] = field(default_factory=list)
    problem_hypothesis: Optional[ProblemHypothesis] = None
    stage_statuses: List[StageStatus] = field(default_factory=list)
    llm_available: bool = True
    degraded: bool = False  # True if any LLM stage failed and fallback was used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archive_name": self.archive_name,
            "generated_at": self.generated_at,
            "llm_available": self.llm_available,
            "degraded": self.degraded,
            "archive_tree": self.archive_tree.to_dict() if self.archive_tree else None,
            "fingerprints": [f.to_dict() for f in self.fingerprints],
            "parser_decisions": [p.to_dict() for p in self.parser_decisions],
            "table_metadata": [t.to_dict() for t in self.table_metadata],
            "schema_roles": [s.to_dict() for s in self.schema_roles],
            "relationships": [r.to_dict() for r in self.relationships],
            "semantic_labels": [s.to_dict() for s in self.semantic_labels],
            "problem_hypothesis": self.problem_hypothesis.to_dict() if self.problem_hypothesis else None,
            "stage_statuses": [s.to_dict() for s in self.stage_statuses],
        }
