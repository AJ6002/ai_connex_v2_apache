"""
tests/test_cuc_completion.py
-----------------------------
Task 3 tests for is_manifest_minimally_complete() and get_missing_keys().

Pass criteria:
- Incomplete CUC (general intent, no task_family, low confidence) → False
- Partial CUC (intent set, no task_family) → False
- Complete CUC (all three conditions) → True
- get_missing_keys() returns the right human-readable labels
- route_after_parser() routes correctly given CUC state + upload_path
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from aiconnex_agent.schemas import ConversationUnderstandingContract, Goal
from aiconnex_agent.parser.cuc_completion import is_manifest_minimally_complete, get_missing_keys


def _make_cuc(primary_intent="general", task_family="", confidence=1.0):
    """Helper: build a CUC with the given goal fields."""
    return ConversationUnderstandingContract(
        goal=Goal(
            primary_intent=primary_intent,
            task_family=task_family,
            confidence=confidence,
        )
    )


class TestIsManifestMinimallyComplete:
    def test_default_cuc_is_incomplete(self):
        """Default CUC (general intent, empty task_family) must be incomplete."""
        cuc = ConversationUnderstandingContract()
        assert is_manifest_minimally_complete(cuc) is False

    def test_intent_set_but_no_task_family(self):
        cuc = _make_cuc(primary_intent="predict", task_family="", confidence=0.9)
        assert is_manifest_minimally_complete(cuc) is False

    def test_task_family_set_but_general_intent(self):
        cuc = _make_cuc(primary_intent="general", task_family="regression", confidence=0.9)
        assert is_manifest_minimally_complete(cuc) is False

    def test_all_set_but_low_confidence(self):
        cuc = _make_cuc(primary_intent="predict", task_family="regression", confidence=0.7)
        assert is_manifest_minimally_complete(cuc) is False

    def test_confidence_exactly_at_threshold(self):
        """Confidence exactly at 0.85 should pass."""
        cuc = _make_cuc(primary_intent="detect_anomalies", task_family="anomaly", confidence=0.85)
        assert is_manifest_minimally_complete(cuc) is True

    def test_full_complete_cuc(self):
        cuc = _make_cuc(primary_intent="train_rul", task_family="regression", confidence=0.92)
        assert is_manifest_minimally_complete(cuc) is True

    def test_empty_string_intent_is_incomplete(self):
        cuc = _make_cuc(primary_intent="", task_family="classification", confidence=0.95)
        assert is_manifest_minimally_complete(cuc) is False


class TestGetMissingKeys:
    def test_all_missing_on_default_cuc(self):
        cuc = ConversationUnderstandingContract()
        missing = get_missing_keys(cuc)
        # primary_intent and task_family should both appear
        joined = " ".join(missing).lower()
        assert "primary task" in joined or "task" in joined
        assert "problem type" in joined or "type" in joined

    def test_only_task_family_missing(self):
        cuc = _make_cuc(primary_intent="predict", task_family="", confidence=0.9)
        missing = get_missing_keys(cuc)
        joined = " ".join(missing).lower()
        assert "problem type" in joined

    def test_empty_when_complete(self):
        cuc = _make_cuc(primary_intent="predict", task_family="regression", confidence=0.9)
        assert get_missing_keys(cuc) == []


class TestGraphRouting:
    def test_route_after_parser_incomplete_cuc(self):
        """Incomplete CUC → clarification_node."""
        from aiconnex_agent.graph import route_after_parser
        from aiconnex_agent.state import MasterAgentState

        state = MasterAgentState()  # default CUC (general, empty)
        assert route_after_parser(state) == "clarification_node"

    def test_route_after_parser_complete_no_upload(self):
        """Complete CUC + no upload → advise_upload_node."""
        from aiconnex_agent.graph import route_after_parser
        from aiconnex_agent.state import MasterAgentState

        state = MasterAgentState(
            cuc=_make_cuc(primary_intent="train_rul", task_family="regression", confidence=0.9),
            upload_path=None,
        )
        assert route_after_parser(state) == "advise_upload_node"

    def test_route_after_parser_complete_with_upload(self):
        """Complete CUC + upload_path set → planning_engine_node."""
        from aiconnex_agent.graph import route_after_parser
        from aiconnex_agent.state import MasterAgentState

        state = MasterAgentState(
            cuc=_make_cuc(primary_intent="detect_anomalies", task_family="anomaly", confidence=0.95),
            upload_path="/tmp/fake_dataset.zip",
        )
        assert route_after_parser(state) == "planning_engine_node"
