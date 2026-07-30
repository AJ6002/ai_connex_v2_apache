"""
aiconnex_agent/state.py - Master LangGraph State Definition
===========================================================
Defines the MasterAgentState Pydantic model integrating the 5-stage contract pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from aiconnex_agent.schemas import (
    ConversationUnderstandingContract,
    ScoutEnrichedContract,
    PreCompilerContract,
    DatasetIntelligenceContract,
)


class MasterAgentState(BaseModel):
    """Master State for LangGraph Orchestration."""
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Chat message history")
    cuc: ConversationUnderstandingContract = Field(default_factory=ConversationUnderstandingContract, description="Stage 1: Pre-Upload CUC")
    scout_enriched: ScoutEnrichedContract = Field(default_factory=ScoutEnrichedContract, description="Stage 2: During Upload Scout Enriched")
    pre_compiler: PreCompilerContract = Field(default_factory=PreCompilerContract, description="Stage 3: Pre-Compiler Contract")
    dic: DatasetIntelligenceContract = Field(default_factory=DatasetIntelligenceContract, description="Stage 4 & 5: Post-Compiler DIC")
    upload_path: Optional[str] = Field(default=None, description="Filesystem path to the real uploaded dataset archive/file, set by the caller before graph invocation (Phase 5b gap 1)")
    active_agent: Optional[str] = Field(default="parser", description="Current active agent/node name")
    current_step_index: int = Field(default=0, description="Step pointer in multi-agent execution plan")
    plan_steps: List[Dict[str, Any]] = Field(default_factory=list, description="List of planned task steps")
    confidence_score: float = Field(default=1.0, description="Overall parser/routing confidence score [0.0 - 1.0]")
    interrupt_reason: Optional[str] = Field(default=None, description="Reason for HITL interrupt if paused")
    memory_context: Dict[str, Any] = Field(default_factory=dict, description="Session and memory bank context")
