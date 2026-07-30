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

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Pre-Upload CUC (Conversation Understanding Contract)
# ---------------------------------------------------------------------------

class ConversationUnderstandingContract(BaseModel):
    """1. Pre-Upload CUC - Built strictly from conversation before upload."""
    conversation: Dict[str, Any] = Field(default_factory=dict, description="Session, prompt and interaction metadata")
    goal: Dict[str, Any] = Field(default_factory=dict, description="User primary goal and task family")
    observed: Dict[str, Any] = Field(default_factory=dict, description="Explicitly mentioned entities, files, columns")
    inferred: Dict[str, Any] = Field(default_factory=dict, description="Inferred domain, target candidates, entity columns")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="User-specified constraints and tolerances")
    dataset_expectation: Dict[str, Any] = Field(default_factory=dict, description="Expected formats, multi-table layout")
    clarifications_required: List[str] = Field(default_factory=list, description="Questions needed from user before compilation")
    planning_hints: Dict[str, Any] = Field(default_factory=dict, description="Hints for downsteam Agent Routing")


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


class BranchingHints(BaseModel):
    available_branches: List[str] = Field(default_factory=list, description="Available recipe branch paths (e.g. A1, B1)")


class DatasetIntelligenceContract(BaseModel):
    """4 & 5. Post-Compiler Contract (DIC) - Output from UnifiedCompiler execution."""
    dataset_identity: DatasetIdentity = Field(default_factory=DatasetIdentity)
    compiled_dataset: CompiledDatasetSummary = Field(default_factory=CompiledDatasetSummary)
    schema_map: Dict[str, str] = Field(default_factory=dict, description="Column -> Data type mapping")
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

