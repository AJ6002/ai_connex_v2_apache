"""
aiconnex_zip_compiler.intelligence - LLM-Driven Dataset Intelligence Layer
==========================================================================
Implements the 7-stage discovery pipeline that runs before/around the
deterministic plugin compiler:

  1. Archive Exploration   (deterministic) - ArchiveExplorer
  2. Format Detection      (magic bytes + LLM for unknowns) - FormatDetector
  3. Parser Selection      (LLM over live plugin catalog) - ParserAdvisor
  4. Metadata Extraction   (deterministic statistics) - MetadataExtractor
  5. Schema Discovery      (LLM role inference) - SchemaAnalyzer
  6. Semantic Analysis     (LLM physical meaning) - SemanticAnalyzer
  7. Problem Discovery     (LLM question + dynamic options) - ProblemDiscoverer

Orchestrated by IntelligenceOrchestrator, which emits
archive_intelligence_report.json.
"""

from .archive_explorer import ArchiveExplorer
from .format_detector import FormatDetector
from .llm_client import (
    LLMClient,
    LLMResponse,
    LLMUnavailableError,
    llm_disabled_by_env,
    reset_availability_cache,
)
from .metadata_extractor import MetadataExtractor
from .models import (
    ArchiveNode,
    ArchiveTree,
    ColumnProfile,
    FileFingerprint,
    GeneratedIntentOption,
    IntelligenceReport,
    ParserDecision,
    PartitionGroup,
    ProblemHypothesis,
    SchemaRoles,
    SemanticLabel,
    StageStatus,
    TableMetadata,
    TableRelationship,
)
from .orchestrator import IntelligenceOrchestrator
from .parser_advisor import ParserAdvisor
from .problem_discoverer import ProblemDiscoverer
from .schema_analyzer import SchemaAnalyzer
from .semantic_analyzer import SemanticAnalyzer
from .validation import (
    dedupe_with_suffix,
    safe_choice,
    safe_confidence,
    slugify,
    stable_slug,
)

__all__ = [
    # Orchestration
    "IntelligenceOrchestrator",
    # Stage components
    "ArchiveExplorer",
    "FormatDetector",
    "ParserAdvisor",
    "MetadataExtractor",
    "SchemaAnalyzer",
    "SemanticAnalyzer",
    "ProblemDiscoverer",
    # LLM
    "LLMClient",
    "LLMResponse",
    "LLMUnavailableError",
    "llm_disabled_by_env",
    "reset_availability_cache",
    # Models
    "ArchiveNode",
    "ArchiveTree",
    "FileFingerprint",
    "ParserDecision",
    "ColumnProfile",
    "TableMetadata",
    "SchemaRoles",
    "TableRelationship",
    "SemanticLabel",
    "PartitionGroup",
    "GeneratedIntentOption",
    "ProblemHypothesis",
    "StageStatus",
    "IntelligenceReport",
    # Validation helpers
    "safe_confidence",
    "safe_choice",
    "slugify",
    "stable_slug",
    "dedupe_with_suffix",
]
