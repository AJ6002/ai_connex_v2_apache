"""
Pydantic models for the Data Dictionary module.

Mirrors the repo's existing schema style (see schemas.py, validation.py).
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Type-specific nested models
# ──────────────────────────────────────────────


class FeatureFields(BaseModel):
    data_type: str = ""
    physical_unit: str = ""
    expected_range: list[float] = Field(default_factory=list)
    null_gate_ratio: float = 0.0
    stuck_limit_rows: int = 0
    imputation_fallback: str = ""


class KnowledgeBaseFields(BaseModel):
    source_path: str = ""
    article_count: int = 0
    search_index_ref: str = ""


class CheatSheetFields(BaseModel):
    source_path: str = ""
    topic: str = ""
    last_verified_date: str = ""


class PolicyManualFields(BaseModel):
    source_path: str = ""
    policy_domain: str = ""
    effective_date: str = ""
    requires_approval_to_edit: bool = False


class SopFields(BaseModel):
    source_path: str = ""
    applies_to_task: str = ""
    steps_count: int = 0


class MacroTemplateFields(BaseModel):
    template_text: str = ""
    use_case: str = ""
    variables: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Shared envelope + union type
# ──────────────────────────────────────────────

EntryType = Literal[
    "feature",
    "knowledge_base",
    "cheat_sheet",
    "policy_manual",
    "sop",
    "macro_template",
]


class DictionaryEntry(BaseModel):
    entry_id: str
    entry_type: EntryType
    display_name: str
    description: str = ""
    created_at: str = ""
    tags: list[str] = Field(default_factory=list)

    # Type-specific fields (all optional — only one set is populated per entry)
    feature_fields: Optional[FeatureFields] = None
    knowledge_base_fields: Optional[KnowledgeBaseFields] = None
    cheat_sheet_fields: Optional[CheatSheetFields] = None
    policy_manual_fields: Optional[PolicyManualFields] = None
    sop_fields: Optional[SopFields] = None
    macro_template_fields: Optional[MacroTemplateFields] = None