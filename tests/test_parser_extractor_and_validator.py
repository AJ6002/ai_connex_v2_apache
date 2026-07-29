# tests/test_parser_extractor_and_validator.py
import pytest
from aiconnex_agent.schemas import ConversationUnderstandingContract
from aiconnex_agent.parser.semantic_extractor import SemanticExtractor
from aiconnex_agent.parser.output_validator import StructuredOutputValidator


def test_semantic_extractor_heuristic_fallback():
    extractor = SemanticExtractor(use_llm=False)
    raw = extractor.extract("upload suyash2.zip archive")
    assert raw["goal"]["primary_intent"] == "compile_zip"
    assert "suyash2.zip" in raw["observed"]["mentioned_files"]


def test_structured_output_validator():
    validator = StructuredOutputValidator()
    raw_dict = {
        "goal": {"raw_prompt": "upload suyash2.zip", "primary_intent": "compile_zip"},
        "observed": {"mentioned_files": ["suyash2.zip"]},
        "inferred": {"domain": "Compressor Telemetry"},
    }
    cuc = validator.validate(raw_dict)
    assert isinstance(cuc, ConversationUnderstandingContract)
    assert cuc.goal["primary_intent"] == "compile_zip"
