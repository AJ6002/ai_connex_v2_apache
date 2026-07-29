# tests/test_parser_scorer_and_generator.py
import pytest
from aiconnex_agent.schemas import ConversationUnderstandingContract
from aiconnex_agent.parser.confidence_scorer import ConfidenceScorer
from aiconnex_agent.parser.clarification_generator import ClarificationGenerator


def test_confidence_scorer_high():
    cuc = ConversationUnderstandingContract(
        goal={"primary_intent": "compile_zip"},
        observed={"mentioned_files": ["suyash2.zip"]}
    )
    scorer = ConfidenceScorer()
    score = scorer.score(cuc)
    assert score >= 0.90


def test_confidence_scorer_low():
    cuc = ConversationUnderstandingContract(
        goal={"primary_intent": "general"},
        observed={"mentioned_files": []}
    )
    scorer = ConfidenceScorer()
    score = scorer.score(cuc)
    assert score < 0.85


def test_clarification_generator():
    cuc = ConversationUnderstandingContract(
        goal={"primary_intent": "general"}
    )
    gen = ClarificationGenerator()
    questions = gen.generate(cuc)
    assert len(questions) >= 1
    assert any("dataset" in q.lower() or "goal" in q.lower() or "would you like" in q.lower() for q in questions)
