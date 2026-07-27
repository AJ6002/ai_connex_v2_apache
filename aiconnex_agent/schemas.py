"""
aiconnex_agent/schemas.py - Canonical Pydantic Schemas for Agent/Backend Communication
========================================================================================
Defines the UserIntentJSON and CompilerOutputJSON Pydantic contracts used across
the LangGraph orchestration framework and CompilerAdapter.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CompilerHints(BaseModel):
    sheet_selection: Optional[str] = Field(default=None, description="Sheet name or preference")
    header_row_depth: Optional[int] = Field(default=None, description="Number of header rows to collapse")
    delta_from_cumulative: Optional[bool] = Field(default=None, description="Whether to compute daily delta from cumulative column")
    formula_error_handling: Optional[str] = Field(default="null_fill", description="Strategy for Excel errors like #DIV/0!")
    dedup_strategy: Optional[str] = Field(default="keep_last", description="Row deduplication strategy")
    include_zero_columns: Optional[bool] = Field(default=True, description="Keep columns with mostly zero values")


class UploadMetadata(BaseModel):
    filename: Optional[str] = Field(default=None, description="Name of uploaded file or zip")
    file_count: Optional[int] = Field(default=None, description="Number of files in archive")
    file_type: Optional[str] = Field(default=None, description="Primary extension")


class UserIntentJSON(BaseModel):
    schema_version: str = Field(default="1.0")
    session_id: str = Field(..., description="Unique session ID")
    user_goal: str = Field(..., description="Raw or parsed goal string from the user")
    task_type: Optional[str] = Field(default="auto", description="time_series | regression | anomaly | clustering | auto")
    target_column: Optional[str] = Field(default=None, description="Specified target column or null for auto-detect")
    entity_column: Optional[str] = Field(default=None, description="Specified entity grouping column")
    time_column: Optional[str] = Field(default=None, description="Specified date/timestamp column")
    domain: Optional[str] = Field(default=None, description="Industrial domain classification")
    upload: Optional[UploadMetadata] = Field(default_factory=UploadMetadata)
    compiler_hints: CompilerHints = Field(default_factory=CompilerHints)
    hitl_answers: Dict[str, Any] = Field(default_factory=dict, description="Answers provided to HITL questions")


class HITLQuestion(BaseModel):
    key: str = Field(..., description="Unique question identifier key (e.g. Q1_sheet_selection)")
    question: str = Field(..., description="Human readable question text")
    options: List[str] = Field(default_factory=list, description="Choice options")
    blocking: bool = Field(default=True, description="Whether this question blocks compilation")
    reason: Optional[str] = Field(default=None, description="Rationale for asking this question")


class CompilerOutputJSON(BaseModel):
    session_id: str = Field(..., description="Session ID matching input")
    status: str = Field(..., description="success | partial | hitl_required | unsupported_format | failed")
    compiled_csv_path: Optional[str] = Field(default=None, description="Absolute or relative path to compiled CSV")
    row_count: Optional[int] = Field(default=None, description="Total row count of compiled dataset")
    column_count: Optional[int] = Field(default=None, description="Total feature column count")
    detected_schema: Dict[str, str] = Field(default_factory=dict, description="Column name -> dtype mapping")
    hitl_required: bool = Field(default=False, description="True if compiler needs human clarification")
    hitl_questions: List[HITLQuestion] = Field(default_factory=list, description="List of questions for the user")
    compiler_decisions: Dict[str, Any] = Field(default_factory=dict, description="Decisions made during compilation")
    warnings: List[str] = Field(default_factory=list, description="Warnings emitted during compilation")
    error: Optional[str] = Field(default=None, description="Error message if status is failed/unsupported_format")
