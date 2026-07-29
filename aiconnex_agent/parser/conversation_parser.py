"""
aiconnex_agent/parser/conversation_parser.py
=============================================
Main Conversation Parser Orchestrator running the 6 sub-modules:
  1. PromptBuilder
  2. ContextManager
  3. SemanticExtractor
  4. StructuredOutputValidator
  5. ConfidenceScorer
  6. ClarificationGenerator
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from aiconnex_agent.state import MasterAgentState
from aiconnex_agent.parser.prompt_builder import PromptBuilder
from aiconnex_agent.parser.context_manager import ContextManager
from aiconnex_agent.parser.semantic_extractor import SemanticExtractor
from aiconnex_agent.parser.output_validator import StructuredOutputValidator
from aiconnex_agent.parser.confidence_scorer import ConfidenceScorer
from aiconnex_agent.parser.clarification_generator import ClarificationGenerator

logger = logging.getLogger(__name__)

# Module Singletons
prompt_builder = PromptBuilder()
context_manager = ContextManager()
semantic_extractor = SemanticExtractor()
output_validator = StructuredOutputValidator()
confidence_scorer = ConfidenceScorer()
clarification_generator = ClarificationGenerator()


def real_conversation_parser_node(state: MasterAgentState) -> Dict[str, Any]:
    """Real Conversation Parser Node running all 6 sub-modules."""
    logger.info("[ConversationParser] Executing 6-module pipeline")
    user_prompt = state.messages[-1]["content"] if state.messages else ""
    
    # 1 & 2. Prompt & Context
    sys_prompt = prompt_builder.build_system_prompt(user_prompt)
    ctx = context_manager.update_context(user_prompt, state.messages)
    
    # 3. Semantic Extraction
    raw_dict = semantic_extractor.extract(user_prompt, sys_prompt)
    
    # 4. Output Validation
    cuc = output_validator.validate(raw_dict)
    
    # 5. Confidence Scoring
    score = confidence_scorer.score(cuc)
    
    # 6. Clarification Generation (if score < 0.85)
    clarifications = []
    if score < 0.85:
        clarifications = clarification_generator.generate(cuc)
        cuc.clarifications_required = clarifications
        
    cuc_dict = cuc.model_dump() if hasattr(cuc, "model_dump") else cuc.dict()
    
    return {
        "cuc": cuc_dict,
        "active_agent": "clarification" if score < 0.85 else "planner",
        "confidence_score": score,
    }
