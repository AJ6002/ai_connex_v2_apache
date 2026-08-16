"""
aiconnex_agent/schemas.py - Exact 5-Stage Contract Pipeline Pydantic Models
=============================================================================
Defines the 5 canonical JSON contracts specified for the AIConnex Agentic Compiler System:
  1. ConversationUnderstandingContract (CUC - Pre-Upload)
  2. ScoutEnrichedContract (During Upload)
  3. PreCompilerContract (Input to UnifiedCompiler)
  4 & 5. DatasetIntelligenceContract (DIC - Post-Compiler Output)
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Pre-Upload CUC (Conversation Understanding Contract)
# ---------------------------------------------------------------------------

class Goal(BaseModel):
    """Goal sub-model inside CUC contract."""
    primary_intent: str = Field(
        default="general",
        description="Canonical primary intent: compile_zip | train_rul | detect_anomalies | predict | query_status | general. "
                     "Used as a routing key (IntentPlanMapper dict lookup) — keep this a controlled vocabulary, not free text.",
    )
    business_goal: str = Field(
        default="",
        description="The user's goal in their own words, e.g. 'Predict Remaining Useful Life'. Free text, stable across "
                     "however the eventual ML formulation turns out (regression vs. survival analysis vs. physics-informed, "
                     "etc.) — that formulation decision is deferred to post-upload (Scout's Recipe Catalog). Distinct from "
                     "primary_intent, which is a coarse routing label, not a business statement.",
    )
    raw_prompt: str = Field(default="", description="Original user prompt verbatim")
    task_family: str = Field(
        default="",
        description="High-level task family label (e.g. regression, anomaly_detection). Non-binding coarse framing used "
                     "only to route to the right pre-upload plan template and required-fields gate — the specific ML "
                     "formulation is still decided post-upload via Scout's Recipe Catalog, not locked in here.",
    )
    confidence: float = Field(default=1.0, description="Extraction confidence [0.0 - 1.0]")


class ContradictionRecord(BaseModel):
    """A single detected contradiction between a previously-merged CUC field
    value and a newly-extracted value for the same field, produced by
    contract_manager_node. Kept as a record instead of silently overwriting,
    so the planner/response_writer can surface it back to the user."""
    field_path: str = Field(..., description="Dotted path of the contradicting field, e.g. 'goal.task_family'")
    previous_value: Any = Field(default=None, description="Value held before this turn")
    new_value: Any = Field(default=None, description="Newly-extracted value this turn")
    turn_detected: int = Field(default=0, description="Conversation turn index at which this was detected")
    resolved: bool = Field(default=False, description="True once the contradiction has been explicitly resolved by the user")


class BusinessContext(BaseModel):
    """Formalized business framing, distinct from the coarse ML-routing fields
    on Goal. Mostly a reorganization of what previously lived loosely inside
    the 'inferred' dict (industry/domain), now given a stable, named shape
    so downstream consumers don't have to guess key names."""
    industry: str = Field(default="", description="e.g. 'Chemical', 'Aerospace Manufacturing'")
    process: str = Field(default="", description="e.g. 'Wastewater Treatment'")
    asset: str = Field(default="", description="e.g. 'RO Plant', 'Turbofan Engine'")
    operational_objective: str = Field(default="", description="e.g. 'Reduce TDS', 'Avoid unplanned downtime'")


class ConversationUnderstandingContract(BaseModel):
    """1. Pre-Upload CUC - Built strictly from conversation before upload."""
    conversation: Dict[str, Any] = Field(default_factory=dict, description="Session, prompt and interaction metadata")
    goal: Goal = Field(default_factory=Goal, description="User primary goal and task family")
    observed: Dict[str, Any] = Field(
        default_factory=dict,
        description="Explicitly mentioned entities/files as the USER STATED them (e.g. 'temperature', 'pressure'). "
                     "Deliberately NOT assumed to match actual dataset column names — those are Scout's job to "
                     "discover post-upload (e.g. user says 'temperature', real column is 'Temp_C'). See "
                     "observed.mentioned_entities / observed.mentioned_files.",
    )
    inferred: Dict[str, Any] = Field(default_factory=dict, description="Inferred domain, target candidates, entity columns")
    business_context: BusinessContext = Field(
        default_factory=BusinessContext,
        description="Formalized business framing (industry/process/asset/operational_objective) for downstream "
                     "recipe/report generation. Not contradiction-checked (see contract_manager.py) — treated like "
                     "'inferred', taking the newest meaningful value each turn.",
    )
    constraints: Dict[str, Any] = Field(default_factory=dict, description="User-specified constraints and tolerances")
    dataset_expectation: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected formats, multi-table layout. Include 'expected_source': 'user_statement' | 'inferred' "
                     "alongside any inferred field (e.g. expected_dataset_type) so consumers know whether the user "
                     "said it directly or the extractor guessed it.",
    )
    clarifications_required: List[str] = Field(default_factory=list, description="Questions needed from user before compilation")
    planning_hints: Dict[str, Any] = Field(default_factory=dict, description="Hints for downsteam Agent Routing")
    contradictions: List[ContradictionRecord] = Field(
        default_factory=list,
        description="Detected field-value contradictions across turns, appended by contract_manager_node. "
                     "Never silently overwritten — merge logic preserves the prior value until resolved.",
    )


# ---------------------------------------------------------------------------
# 1b. Pre-Upload v1 Architecture: Conversation Plan + Upload Readiness Contract
# ---------------------------------------------------------------------------

class ConversationPlan(BaseModel):
    """Output of conversation_planner_node: the single decision for what
    should happen next in the conversation, replacing the old binary
    confidence-threshold branch with an explicit, inspectable action.
    Consumed by response_writer_node (ask/summarize/confirm) or
    upload_gate_node (recommend_upload)."""
    action: Literal["ask", "summarize", "confirm", "recommend_upload", "wait"] = Field(
        ..., description="The single next conversational action decided by the planner"
    )
    target_field: Optional[str] = Field(
        default=None, description="Dotted CUC field path this action concerns, e.g. 'goal.task_family' (set when action='ask')"
    )
    rationale: str = Field(default="", description="Short human-readable reason for this decision (for logs/debugging)")
    missing_required_fields: List[str] = Field(
        default_factory=list, description="Required fields (per Required Fields Registry) still unfilled at decision time"
    )


class UploadReadinessContract(BaseModel):
    """Formal pre-upload exit artifact. Produced alongside/after a
    ConversationPlan with action='recommend_upload'. Distinct from the
    InterruptPayload sent over interrupt() — this is the persisted,
    inspectable state field; the InterruptPayload is just its HITL transport."""
    ready: bool = Field(default=False, description="True once Upload Readiness Rules are satisfied")
    missing_fields: List[str] = Field(default_factory=list, description="Required fields still missing when ready=False")
    evaluated_at_turn: int = Field(default=0, description="Conversation turn index this evaluation was made at")


# ---------------------------------------------------------------------------
# 2. Upload & Scout Agent Enriched Sub-Models
# ---------------------------------------------------------------------------

class UploadMetadata(BaseModel):
    status: str = Field(default="uploaded", description="uploaded | pending | failed")
    upload_time: str = Field(default="", description="ISO timestamp")
    archive_name: str = Field(default="", description="File name of uploaded archive")
    archive_type: str = Field(default="", description="zip | csv | xlsx | mat | parquet | tdms")
    archive_size: str = Field(default="", description="Human-readable file size")
    checksum: str = Field(default="", description="SHA-256 or MD5 hash")


class ArchiveDiscovery(BaseModel):
    root_structure: List[str] = Field(default_factory=list, description="Top-level folders/files")
    files_detected: List[str] = Field(default_factory=list, description="All discovered file paths")
    directories: List[str] = Field(default_factory=list, description="All discovered subdirectories")
    total_files: int = Field(default=0, description="Total file count in archive")


class FileInventoryItem(BaseModel):
    filename: str = Field(default="", description="Relative path of file")
    type: str = Field(default="", description="File extension / format")
    role: str = Field(default="", description="fact_table | dimension | metadata | unknown")
    parser_candidate: str = Field(default="", description="Recommended parser plugin ID")


class ParserSelection(BaseModel):
    selected_parsers: List[str] = Field(default_factory=list, description="List of chosen parser plugins")
    unsupported_files: List[str] = Field(default_factory=list, description="List of unparseable files")
    confidence: float = Field(default=0.0, description="Parser selection confidence score [0.0 - 1.0]")


class ScoutEnrichedContract(BaseModel):
    """2. During Upload Contract - Appends upload, discovery & parser selection to CUC."""
    conversation_contract: ConversationUnderstandingContract = Field(default_factory=ConversationUnderstandingContract)
    upload: UploadMetadata = Field(default_factory=UploadMetadata)
    archive_discovery: ArchiveDiscovery = Field(default_factory=ArchiveDiscovery)
    file_inventory: List[FileInventoryItem] = Field(default_factory=list)
    parser_selection: ParserSelection = Field(default_factory=ParserSelection)


# ---------------------------------------------------------------------------
# 3. Pre-Compiler Contract
# ---------------------------------------------------------------------------

class CompilerRequest(BaseModel):
    compile_mode: str = Field(default="automatic", description="automatic | interactive | batch")
    canonical_schema: bool = Field(default=True, description="Enforce snake_case & ISO 8601 timestamps")
    generate_dataset_card: bool = Field(default=True, description="Emit dataset_card.json")
    generate_statistics: bool = Field(default=True, description="Compute column null/duplicate statistics")
    infer_problem_candidates: bool = Field(default=True, description="Detect Regression/Anomaly/Hybrid tracks")
    infer_targets: bool = Field(default=True, description="Identify target column candidates")
    generate_quality_report: bool = Field(default=True, description="Emit join & quality audit report")


class PreCompilerContract(BaseModel):
    """3. Pre-Compiler Contract - Enriched Contract + CompilerRequest passed to UnifiedCompiler."""
    conversation_contract: ConversationUnderstandingContract = Field(default_factory=ConversationUnderstandingContract)
    upload: UploadMetadata = Field(default_factory=UploadMetadata)
    archive_discovery: ArchiveDiscovery = Field(default_factory=ArchiveDiscovery)
    file_inventory: List[FileInventoryItem] = Field(default_factory=list)
    parser_selection: ParserSelection = Field(default_factory=ParserSelection)
    compiler_request: CompilerRequest = Field(default_factory=CompilerRequest)


# ---------------------------------------------------------------------------
# 4 & 5. Post-Compiler Contract (Dataset Intelligence Contract - DIC)
# ---------------------------------------------------------------------------

class DatasetIdentity(BaseModel):
    name: str = Field(default="", description="Name of compiled dataset")
    family: str = Field(default="", description="Domain classification (e.g. Aircraft Engine Prognostics)")
    domain: Optional[str] = Field(default=None, description="Industrial sub-domain")


class CompiledDatasetSummary(BaseModel):
    tables: int = Field(default=0, description="Number of compiled condition tables")
    rows: int = Field(default=0, description="Total compiled record count")
    columns: int = Field(default=0, description="Total feature column count")
    output_path: Optional[str] = Field(default=None, description="Output directory path")
    combined_csv_path: Optional[str] = Field(default=None, description="Path to all_groups_combined.csv")


class DatasetStatistics(BaseModel):
    missing_values: Dict[str, int] = Field(default_factory=dict, description="Null count per column")
    duplicates: int = Field(default=0, description="Duplicate row count")
    sampling: str = Field(default="unknown", description="Sampling rate/pattern (e.g. per_cycle, 3min)")


class QualityReport(BaseModel):
    constant_columns: List[str] = Field(default_factory=list, description="Zero variance columns")
    warnings: List[str] = Field(default_factory=list, description="Compilation warnings")
    cartesian_guard_passed: bool = Field(default=True, description="Whether Cartesian explosion guard passed")


class ProblemCandidate(BaseModel):
    family: str = Field(..., description="Regression | Anomaly | Hybrid | Time_Series")
    confidence: float = Field(..., description="Confidence score [0.0 - 1.0]")


class AnalyticalRecipe(BaseModel):
    """A candidate analytical objective derived from the compiled dataset — the user picks one."""
    id: str = Field(..., description="Unique recipe identifier e.g. R001")
    title: str = Field(..., description="Human-readable objective title")
    target: Optional[str] = Field(default=None, description="Target column for supervised tasks; None for unsupervised")
    task: str = Field(..., description="REGRESSION | CLASSIFICATION | ANOMALY | FORECAST | HYBRID")
    confidence: float = Field(default=1.0, description="Confidence that this objective applies to the dataset")
    rationale: str = Field(default="", description="One-line reasoning for why this recipe was surfaced")


class BranchingHints(BaseModel):
    available_branches: List[str] = Field(default_factory=list, description="Available recipe branch paths (e.g. A1, B1)")


class DatasetIntelligenceContract(BaseModel):
    """4 & 5. Post-Compiler Contract (DIC) - Output from UnifiedCompiler execution."""
    dataset_identity: DatasetIdentity = Field(default_factory=DatasetIdentity)
    compiled_dataset: CompiledDatasetSummary = Field(default_factory=CompiledDatasetSummary)
    schema_map: Dict[str, str] = Field(default_factory=dict, description="Column -> inferred dtype (datetime | numeric | categorical | text)")
    dataset_card: Dict[str, Any] = Field(default_factory=dict, description="Full dataset_card.json metadata")
    statistics: DatasetStatistics = Field(default_factory=DatasetStatistics)
    quality_report: QualityReport = Field(default_factory=QualityReport)
    derived_features: List[str] = Field(default_factory=list, description="Synthesized features (e.g. rul_piecewise)")
    problem_candidates: List[ProblemCandidate] = Field(default_factory=list, description="ML task track recommendations")
    target_candidates: List[str] = Field(default_factory=list, description="Recommended target columns")
    feature_catalog: Dict[str, Any] = Field(default_factory=dict, description="Categorized feature descriptions")
    branching_hints: BranchingHints = Field(default_factory=BranchingHints)
    compiler_warnings: List[str] = Field(default_factory=list)
    clarifications_required: List[str] = Field(default_factory=list)
    recipes: List[AnalyticalRecipe] = Field(
        default_factory=list,
        description="Data-driven catalog of analytical objectives generated by RecipeCatalogBuilder"
    )
    selected_recipe_id: Optional[str] = Field(
        default=None,
        description="Recipe ID chosen by the user during HITL (e.g. R001)"
    )


# ---------------------------------------------------------------------------
# 6. Planning Engine Contracts
# ---------------------------------------------------------------------------

from typing import Literal


class TaskStep(BaseModel):
    """A single routed unit of work targeting one downstream agent."""
    step_id: str = Field(..., description="Sequential step identifier, e.g. step_1")
    target_agent: Literal["scout", "platform", "memory"] = Field(..., description="Agent responsible for this step")
    task: str = Field(..., description="Human-readable task description")


class ExecutionPlan(BaseModel):
    """Ordered set of TaskSteps produced by the Planning Engine for one CUC."""
    steps: List[TaskStep] = Field(default_factory=list)
    source_intent: str = Field(default="general", description="primary_intent that produced this plan")


# ---------------------------------------------------------------------------
# 6b. HITL Interrupt Contracts
# ---------------------------------------------------------------------------

class InterruptOption(BaseModel):
    """Option choice inside an InterruptPayload."""
    option_id: str = Field(..., description="Unique option identifier")
    label: str = Field(..., description="Human-readable option title")
    description: str = Field(default="", description="Detailed description of option")


class InterruptPayload(BaseModel):
    """Typed LangGraph HITL Interrupt Payload passed to interrupt()."""
    interrupt_type: str = Field(
        default="strategy_choice",
        description="Type of interrupt: strategy_choice | compile_failure | clarification"
    )
    questions: List[str] = Field(default_factory=list, description="Questions presented to user")
    options: List[InterruptOption] = Field(default_factory=list, description="Interactive choices available")
    reason: str = Field(default="", description="Technical rationale for interrupt")



# ---------------------------------------------------------------------------
# 7. Phase 5c: Multi-Candidate Ensemble & Evaluation Triad Contracts
# ---------------------------------------------------------------------------


class CandidateRecipe(BaseModel):
    """A single candidate DAG recipe resolved for parallel training."""
    recipe_id: str = Field(..., description="Unique recipe identifier, e.g. recipe_dag414_lgbm")
    dag_id: str = Field(..., description="DAG ID from dag_conditions_mapping.json, e.g. DAG_414")
    algo_family: str = Field(..., description="Algorithm family, e.g. REGRESSION, ANOMALY DETECTION")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Algorithm hyperparameters")
    feature_config: Dict[str, Any] = Field(default_factory=dict, description="Feature engineering config (lags, rolling, etc.)")


class ScorerReport(BaseModel):
    """Hard quantitative metrics for one trained candidate model."""
    recipe_id: str = Field(..., description="Recipe that produced this model")
    r2_score: float = Field(..., description="R² coefficient of determination")
    rmse: float = Field(..., description="Root Mean Squared Error")
    mae: float = Field(..., description="Mean Absolute Error")
    mape: float = Field(..., description="Mean Absolute Percentage Error")
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")
    model_size_mb: float = Field(default=0.0, description="Serialized model binary size in MB")


class JudgeReport(BaseModel):
    """LLM-based qualitative risk evaluation for one candidate model."""
    recipe_id: str = Field(..., description="Recipe that produced this model")
    qualitative_score: float = Field(default=0.5, description="Overall qualitative score [0.0 - 1.0]")
    rubric_ratings: Dict[str, float] = Field(default_factory=dict, description="Per-rubric scores")
    reasoning: str = Field(default="", description="LLM reasoning text")
    risk_assessment: str = Field(default="", description="Risk summary")


class LeaderboardEntry(BaseModel):
    """A single row in the multi-candidate competition leaderboard."""
    rank: int = Field(..., description="1-indexed rank position")
    model_id: str = Field(..., description="Unique model identifier")
    dag_id: str = Field(..., description="DAG ID that produced this model")
    algo_name: str = Field(..., description="Human-readable algorithm name")
    composite_score: float = Field(..., description="MCDA composite score")
    r2_score: float = Field(default=0.0)
    rmse: float = Field(default=0.0)
    mae: float = Field(default=0.0)
    is_winner: bool = Field(default=False, description="True for the selected winner")


class SelectionResult(BaseModel):
    """Output of the Selector Agent: the winner and full leaderboard."""
    winner_model_id: str = Field(..., description="Model ID of the selected winner")
    winner_dag_id: str = Field(..., description="DAG ID of the winner")
    is_ensemble: bool = Field(default=False, description="True if winner is the Stacked Ensemble")
    selection_rationale: str = Field(default="", description="Human-readable rationale for selection")
    leaderboard: List[LeaderboardEntry] = Field(default_factory=list, description="Full ranked leaderboard")


# ---------------------------------------------------------------------------
# 8. Scout 8-Node Split — Sub-Manifests + Master Exploration Manifest (Tasks 2-10)
# ---------------------------------------------------------------------------
# Each Scout analysis node produces one of these typed artifacts. The final
# exploration_synthesizer_node combines them into a DatasetExplorationManifest.
# Nothing in these schemas is hardcoded per domain — all fields derive from
# the dataset the user actually uploaded.


# --- Archive Discovery (Task 2) ---

class ArchiveInventoryItem(BaseModel):
    path: str = Field(default="", description="Path relative to the archive root (or absolute for single-file uploads)")
    size_bytes: int = Field(default=0)
    format: str = Field(default="unknown", description="csv | xlsx | parquet | mat | tdms | json | txt | unknown")
    role_hint: str = Field(default="unknown", description="Coarse guess: fact_table | dimension | metadata | unknown")


class ArchiveManifest(BaseModel):
    """Pure file-system inspection of the uploaded artifact. No data parsing."""
    manifest_type: str = Field(default="archive_manifest")
    archive_path: str = Field(default="")
    archive_type: str = Field(default="unknown", description="zip | folder | single_file | unknown")
    archive_size_bytes: int = Field(default=0)
    checksum: str = Field(default="", description="Hash of the archive for reproducibility")
    files: List[ArchiveInventoryItem] = Field(default_factory=list)
    directories: List[str] = Field(default_factory=list)
    total_files: int = Field(default=0)
    duplicate_files: List[str] = Field(default_factory=list, description="Paths with identical name/size — potential dupes")
    parser_candidates: Dict[str, str] = Field(default_factory=dict, description="filename -> parser plugin id")
    integrity_ok: bool = Field(default=True, description="False if the archive failed integrity checks")
    integrity_notes: List[str] = Field(default_factory=list)


# --- Structure Analysis (Task 3) ---

class TableSchema(BaseModel):
    filename: str = Field(default="", description="Basename of the parsed source file")
    columns: Dict[str, str] = Field(default_factory=dict, description="column_name -> pandas dtype string")
    row_count: int = Field(default=0)


class StructureAnalysis(BaseModel):
    """Output of the parser+compile phase. Points at the compiled CSV on disk;
    downstream analysis nodes read it from there instead of carrying frames in state."""
    manifest_type: str = Field(default="structure_analysis")
    compiled_csv_path: Optional[str] = Field(default=None, description="Path to the combined/compiled CSV")
    output_dir: Optional[str] = Field(default=None)
    tables: List[TableSchema] = Field(default_factory=list, description="Per-source-file schema slices")
    combined_columns: Dict[str, str] = Field(default_factory=dict, description="Final combined-CSV schema: col -> dtype")
    combined_rows: int = Field(default=0)
    warnings: List[str] = Field(default_factory=list)
    compile_success: bool = Field(default=True)


# --- Entity Analysis (Task 4) ---

class EntityRole(BaseModel):
    column: str = ""
    role: str = Field(default="unknown", description="entity_id | timestamp | measurement | dimension | target_candidate | metadata | unknown")
    confidence: float = Field(default=0.0)
    reason: str = Field(default="")


class EntityInventory(BaseModel):
    """Column-level role classification: which columns are entities, timestamps,
    measurements, targets, or metadata. Drives every downstream analysis."""
    manifest_type: str = Field(default="entity_inventory")
    columns: List[EntityRole] = Field(default_factory=list)
    entity_id_columns: List[str] = Field(default_factory=list)
    timestamp_columns: List[str] = Field(default_factory=list)
    measurement_columns: List[str] = Field(default_factory=list)
    dimension_columns: List[str] = Field(default_factory=list)
    target_candidate_columns: List[str] = Field(default_factory=list)
    metadata_columns: List[str] = Field(default_factory=list)


# --- Relationship Analysis (Task 5) ---

class RelationshipEdge(BaseModel):
    from_table: str = ""
    from_column: str = ""
    to_table: str = ""
    to_column: str = ""
    edge_type: str = Field(default="", description="fk_candidate | shared_key | entity_link")
    overlap_score: float = Field(default=0.0, description="Fraction of from_column values present in to_column [0-1]")
    reason: str = Field(default="")


class RelationshipGraph(BaseModel):
    """Inter-table and inter-column relationships. Empty for single-file uploads."""
    manifest_type: str = Field(default="relationship_graph")
    edges: List[RelationshipEdge] = Field(default_factory=list)
    is_multi_table: bool = Field(default=False)
    table_count: int = Field(default=0)


# --- Temporal Analysis (Task 6) ---

class TemporalStructure(BaseModel):
    """Time-series structure detection. is_time_series=False for tabular data."""
    manifest_type: str = Field(default="temporal_structure")
    is_time_series: bool = Field(default=False)
    timestamp_columns: List[str] = Field(default_factory=list)
    primary_timestamp: Optional[str] = Field(default=None)
    detected_frequency: Optional[str] = Field(default=None, description="e.g. 'daily', 'hourly', 'per_cycle', 'irregular'")
    frequency_confidence: float = Field(default=0.0)
    has_gaps: bool = Field(default=False)
    monotonic: bool = Field(default=False)
    date_range: Optional[str] = Field(default=None)
    seasonality_hints: List[str] = Field(default_factory=list, description="e.g. 'weekly', 'monthly'")


# --- Feature Analysis (Task 7) ---

class FeatureEntry(BaseModel):
    column: str = ""
    category: str = Field(default="raw", description="raw | derived | lagged | rolling | encoded")
    dtype: str = Field(default="")
    role: str = Field(default="feature", description="feature | target_candidate | entity | metadata")
    description: str = Field(default="")


class DerivedFeatureCandidate(BaseModel):
    name: str = ""
    source_columns: List[str] = Field(default_factory=list)
    kind: str = Field(default="", description="lag | rolling_mean | diff | ratio | interaction | encoding")
    rationale: str = Field(default="")


class FeatureCatalogV2(BaseModel):
    """Feature-level catalog produced by feature_analysis_node. Named V2 to
    disambiguate from the loose Dict on the legacy DIC."""
    manifest_type: str = Field(default="feature_catalog")
    features: List[FeatureEntry] = Field(default_factory=list)
    derived_candidates: List[DerivedFeatureCandidate] = Field(default_factory=list)
    redundant_pairs: List[List[str]] = Field(default_factory=list, description="Pairs of columns with correlation >= 0.95")


# --- Quality Analysis (Task 8) ---

class QualityIssue(BaseModel):
    kind: str = Field(default="", description="null | duplicate | outlier | constant | imbalance")
    column: Optional[str] = Field(default=None)
    severity: str = Field(default="info", description="info | warning | error")
    detail: str = Field(default="")


class QualityAssessment(BaseModel):
    """Data-quality report. `passed=False` = at least one 'error'-severity issue."""
    manifest_type: str = Field(default="quality_assessment")
    issues: List[QualityIssue] = Field(default_factory=list)
    null_percentages: Dict[str, float] = Field(default_factory=dict, description="col -> pct null (0.0-1.0)")
    duplicate_row_count: int = Field(default=0)
    constant_columns: List[str] = Field(default_factory=list)
    outlier_summary: Dict[str, int] = Field(default_factory=dict, description="col -> count of IQR outliers")
    imbalance_notes: List[str] = Field(default_factory=list)
    passed: bool = Field(default=True)


# --- Statistical Analysis (Task 9) ---

class ColumnStats(BaseModel):
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    skew: Optional[float] = None
    kurtosis: Optional[float] = None
    count: int = 0
    coefficient_of_variation: Optional[float] = None


class CorrelationPair(BaseModel):
    col_a: str = ""
    col_b: str = ""
    r: float = 0.0


class StatisticalProfile(BaseModel):
    """Distributions, correlations, and shape-of-data metrics."""
    manifest_type: str = Field(default="statistical_profile")
    per_column: Dict[str, ColumnStats] = Field(default_factory=dict)
    high_correlation_pairs: List[CorrelationPair] = Field(default_factory=list, description="|r| >= 0.85")
    sampled: bool = Field(default=False, description="True if analysis was run on a sample rather than the full dataset")
    sample_size: int = Field(default=0)
    total_rows: int = Field(default=0)


# --- Pipeline Lock Manifest (Task 11) ---

class PipelineLockManifest(BaseModel):
    """Formal audit boundary between 'user chose this' and 'system executed this'.
    Produced by pipeline_lock_node immediately after HITL completes; once set,
    downstream nodes read from this instead of the raw HITL contract so their
    inputs cannot silently shift under them.
    """
    manifest_type: str = Field(default="pipeline_lock")
    schema_version: str = Field(default="1.0")
    session_id: Optional[str] = Field(default=None)

    # The frozen decision
    locked_recipe_id: str = Field(..., description="Recipe.id chosen by the user from the DIC catalog")
    business_objective: str = Field(
        default="",
        description="User's own-words statement of what they want (from CUC.goal.business_goal or the recipe title)",
    )
    selected_workflow_type: str = Field(
        default="",
        description="Coarse task family from the chosen recipe (regression | anomaly | forecast | classification | hybrid)",
    )
    target_column: Optional[str] = Field(
        default=None,
        description="Target column from the chosen recipe (None for unsupervised tasks like anomaly detection)",
    )
    operational_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any recipe-specific follow-up preferences captured during HITL",
    )
    success_metrics: List[str] = Field(default_factory=list)

    # Audit trail
    locked_at: str = Field(default="", description="ISO-8601 UTC timestamp of when the lock was set")
    locked_by: str = Field(default="user", description="user | system_auto — provenance of the decision")
    hitl_turn_count: int = Field(default=0, description="Number of HITL turns taken to reach the lock")


# --- Workflow Planner (Task 12) ---

class WorkflowStage(BaseModel):
    """One stage in a technical execution workflow.

    The schema supports arbitrary DAG structure via `depends_on`. v1's planner
    only produces linear 3-stage workflows, but v2's compound workflows (e.g.
    anomaly -> health -> RUL -> maintenance_schedule for predictive maintenance)
    are expressible without a breaking schema change.
    """
    stage_id: str = Field(..., description="Unique identifier within the workflow (e.g. 'stage_1', 'anomaly')")
    task: str = Field(..., description="Task name — e.g. feature_engineering | train | evaluate | detect_anomalies")
    depends_on: List[str] = Field(default_factory=list, description="stage_ids this stage waits for; empty = starts immediately")
    config: Dict[str, Any] = Field(default_factory=dict, description="Stage-specific config (target_column, hyperparameters, etc.)")


class WorkflowManifest(BaseModel):
    """Technical execution plan derived from a PipelineLockManifest.

    v1 scope: single-stage or 3-stage linear workflow per locked recipe.
    Multi-stage compound workflows (with real depends_on DAG structure) are
    v2 work — the schema is ready for them but the planner logic isn't yet.
    """
    manifest_type: str = Field(default="workflow_manifest")
    schema_version: str = Field(default="1.0")
    session_id: Optional[str] = Field(default=None)
    locked_recipe_id: str = Field(default="", description="From the PipelineLockManifest this workflow was planned from")
    stages: List[WorkflowStage] = Field(default_factory=list)
    total_stages: int = Field(default=0)
    parallel_possible: bool = Field(
        default=False,
        description="True if any stages have no shared dependency edges (v1 always False for linear workflows)",
    )
    planner_notes: List[str] = Field(default_factory=list, description="Human-readable notes about how the plan was derived")


# --- Master Exploration Manifest (Task 10) ---

class DatasetExplorationManifest(BaseModel):
    """The final, canonical output of the 8-node Scout chain. All sub-manifests
    combined into one auditable artifact, plus the derived RecipeCatalog."""
    manifest_type: str = Field(default="dataset_exploration_manifest")
    schema_version: str = Field(default="1.0")
    session_id: Optional[str] = None
    archive: ArchiveManifest = Field(default_factory=ArchiveManifest)
    structure: StructureAnalysis = Field(default_factory=StructureAnalysis)
    entities: EntityInventory = Field(default_factory=EntityInventory)
    relationships: RelationshipGraph = Field(default_factory=RelationshipGraph)
    temporal: TemporalStructure = Field(default_factory=TemporalStructure)
    features: FeatureCatalogV2 = Field(default_factory=FeatureCatalogV2)
    quality: QualityAssessment = Field(default_factory=QualityAssessment)
    statistics: StatisticalProfile = Field(default_factory=StatisticalProfile)
    recipes: List[AnalyticalRecipe] = Field(default_factory=list, description="Derived by the synthesizer from all 8 analysis outputs")

