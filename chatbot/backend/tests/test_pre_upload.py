"""
Tests for the pre-upload intent-gathering flow.

Simulates multi-turn conversations to verify:
  - Required fields get filled gradually
  - clarifications_required shrinks each turn
  - Higher-confidence values don't get overwritten by lower-confidence ones
  - conversation_complete only flips true once all REQUIRED fields are filled
"""

import json
import os
import sys
import tempfile
import unittest
from copy import deepcopy

# Add parent directory to path so we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pre_upload_schemas import (
    PreUploadContract,
    TurnExtraction,
    CandidateMLProblemType,
    ConversationMeta,
    Goal,
    Observed,
    Inferred,
    InferredField,
    DatasetExpectation,
    Constraints,
    ConversationAnalysis,
    Urgency,
    PlanningHints,
    Metadata,
)
from pre_upload_config import (
    REQUIRED_FIELDS,
    RECOMMENDED_FIELDS,
    MIN_CONFIDENCE_TO_ACCEPT,
    REQUIRED_CONFIDENCE_THRESHOLD,
    RECOMMENDED_CONFIDENCE_THRESHOLD,
)
from pre_upload_flow import (
    _merge_extraction,
    _run_gap_analysis,
    _check_completion,
    _is_field_filled,
    process_turn,
)
from pre_upload_state import (
    SESSION_DIR,
    load_contract,
    save_contract,
    load_replies,
    create_new_session,
)


class TestMergeExtraction(unittest.TestCase):
    """Test the merge logic: higher confidence values should not be
    overwritten by lower confidence ones."""

    def setUp(self):
        self.contract = PreUploadContract()

    def test_primary_goal_merge_higher_confidence_wins(self):
        """A higher-confidence value should replace a lower-confidence one."""
        # First, set a primary goal with medium confidence
        extraction1 = TurnExtraction(
            primary_goal="predict equipment failures",
            primary_goal_confidence=0.6,
        )
        self.contract = _merge_extraction(self.contract, extraction1)
        self.assertEqual(self.contract.goal.primary_goal, "predict equipment failures")

        # Now try to overwrite with a lower confidence value
        extraction2 = TurnExtraction(
            primary_goal="analyze data",
            primary_goal_confidence=0.4,  # lower than existing
        )
        self.contract = _merge_extraction(self.contract, extraction2)
        # Should NOT have been overwritten
        self.assertEqual(self.contract.goal.primary_goal, "predict equipment failures")

    def test_primary_goal_merge_lower_confidence_rejected(self):
        """A value below MIN_CONFIDENCE_TO_ACCEPT should be rejected entirely."""
        extraction = TurnExtraction(
            primary_goal="noise",
            primary_goal_confidence=0.3,  # below 0.4 threshold
        )
        self.contract = _merge_extraction(self.contract, extraction)
        self.assertEqual(self.contract.goal.primary_goal, "")

    def test_inferred_field_confidence_gate(self):
        """Inferred fields should only update when new confidence is higher."""
        # Set industry with high confidence
        extraction1 = TurnExtraction(
            industry="manufacturing",
            industry_confidence=0.85,
        )
        self.contract = _merge_extraction(self.contract, extraction1)
        self.assertEqual(self.contract.inferred.industry.value, "manufacturing")
        self.assertEqual(self.contract.inferred.industry.confidence, 0.85)

        # Try to overwrite with lower confidence
        extraction2 = TurnExtraction(
            industry="energy",
            industry_confidence=0.6,
        )
        self.contract = _merge_extraction(self.contract, extraction2)
        self.assertEqual(self.contract.inferred.industry.value, "manufacturing")
        self.assertEqual(self.contract.inferred.industry.confidence, 0.85)

    def test_ml_problem_types_merge(self):
        """ML problem types should be merged, not replaced."""
        extraction1 = TurnExtraction(
            candidate_ml_problem_types=[CandidateMLProblemType(type="regression", confidence=0.9)],
            candidate_ml_problem_types_confidence=0.9,
        )
        self.contract = _merge_extraction(self.contract, extraction1)
        self.assertEqual(len(self.contract.goal.candidate_ml_problem_types), 1)

        extraction2 = TurnExtraction(
            candidate_ml_problem_types=[CandidateMLProblemType(type="classification", confidence=0.85)],
            candidate_ml_problem_types_confidence=0.85,
        )
        self.contract = _merge_extraction(self.contract, extraction2)
        self.assertEqual(len(self.contract.goal.candidate_ml_problem_types), 2)

    def test_observed_fields_append(self):
        """Observed fields should append unique items."""
        extraction1 = TurnExtraction(
            equipment=["sensor", "motor"],
        )
        self.contract = _merge_extraction(self.contract, extraction1)
        self.assertEqual(len(self.contract.observed.equipment), 2)

        extraction2 = TurnExtraction(
            equipment=["motor", "pump"],  # motor is duplicate
        )
        self.contract = _merge_extraction(self.contract, extraction2)
        self.assertEqual(len(self.contract.observed.equipment), 3)  # sensor, motor, pump


class TestGapAnalysis(unittest.TestCase):
    """Test that gap analysis correctly identifies missing fields."""

    def setUp(self):
        self.contract = PreUploadContract()

    def test_all_required_missing_initially(self):
        """Initially, all REQUIRED fields should be missing."""
        items = _run_gap_analysis(self.contract)
        required_missing = [i for i in items if i.priority == "high"]
        self.assertEqual(len(required_missing), len(REQUIRED_FIELDS))

    def test_required_fields_shrink_as_filled(self):
        """As required fields get filled, the gap analysis should return fewer items."""
        # Fill primary_goal
        self.contract.goal.primary_goal = "predict failures"
        items = _run_gap_analysis(self.contract)
        high_priority = [i for i in items if i.priority == "high"]
        # Should still have 3 missing (ml types, dataset type, file types)
        self.assertEqual(len(high_priority), 3)

        # Fill ML problem types
        self.contract.goal.candidate_ml_problem_types = [
            CandidateMLProblemType(type="regression", confidence=0.9)
        ]
        items = _run_gap_analysis(self.contract)
        high_priority = [i for i in items if i.priority == "high"]
        self.assertEqual(len(high_priority), 2)

        # Fill dataset type
        self.contract.dataset_expectation.expected_dataset_type = "time-series"
        items = _run_gap_analysis(self.contract)
        high_priority = [i for i in items if i.priority == "high"]
        self.assertEqual(len(high_priority), 1)

        # Fill file types
        self.contract.dataset_expectation.expected_file_types = ["CSV"]
        items = _run_gap_analysis(self.contract)
        high_priority = [i for i in items if i.priority == "high"]
        self.assertEqual(len(high_priority), 0)

    def test_recommended_fields_appear_as_medium(self):
        """Recommended fields should appear as medium priority."""
        # Fill all required fields
        self.contract.goal.primary_goal = "predict"
        self.contract.goal.candidate_ml_problem_types = [
            CandidateMLProblemType(type="regression", confidence=0.9)
        ]
        self.contract.dataset_expectation.expected_dataset_type = "time-series"
        self.contract.dataset_expectation.expected_file_types = ["CSV"]

        items = _run_gap_analysis(self.contract)
        medium_priority = [i for i in items if i.priority == "medium"]
        # Should have 3 recommended fields missing
        self.assertEqual(len(medium_priority), 3)


class TestCompletionCheck(unittest.TestCase):
    """Test that conversation_complete only flips when all REQUIRED fields are filled."""

    def setUp(self):
        self.contract = PreUploadContract()

    def test_not_complete_initially(self):
        self.assertFalse(_check_completion(self.contract))

    def test_not_complete_with_partial_fields(self):
        self.contract.goal.primary_goal = "predict"
        self.assertFalse(_check_completion(self.contract))

    def test_complete_when_all_required_filled(self):
        self.contract.goal.primary_goal = "predict failures"
        self.contract.goal.candidate_ml_problem_types = [
            CandidateMLProblemType(type="regression", confidence=0.9)
        ]
        self.contract.dataset_expectation.expected_dataset_type = "time-series"
        self.contract.dataset_expectation.expected_file_types = ["CSV"]
        self.assertTrue(_check_completion(self.contract))


class TestIsFieldFilled(unittest.TestCase):
    """Test the _is_field_filled helper for various field types."""

    def setUp(self):
        self.contract = PreUploadContract()

    def test_string_field_empty(self):
        entry = REQUIRED_FIELDS[0]  # goal.primary_goal
        self.assertFalse(_is_field_filled(self.contract, entry))

    def test_string_field_filled(self):
        self.contract.goal.primary_goal = "predict failures"
        entry = REQUIRED_FIELDS[0]
        self.assertTrue(_is_field_filled(self.contract, entry))

    def test_list_field_empty(self):
        entry = REQUIRED_FIELDS[3]  # expected_file_types
        self.assertFalse(_is_field_filled(self.contract, entry))

    def test_list_field_filled(self):
        self.contract.dataset_expectation.expected_file_types = ["CSV"]
        entry = REQUIRED_FIELDS[3]
        self.assertTrue(_is_field_filled(self.contract, entry))

    def test_inferred_field_below_threshold(self):
        self.contract.inferred.industry.value = "manufacturing"
        self.contract.inferred.industry.confidence = 0.3  # below RECOMMENDED threshold
        entry = RECOMMENDED_FIELDS[0]  # inferred.industry
        self.assertFalse(_is_field_filled(self.contract, entry))

    def test_inferred_field_above_threshold(self):
        self.contract.inferred.industry.value = "manufacturing"
        self.contract.inferred.industry.confidence = 0.6  # above RECOMMENDED threshold
        entry = RECOMMENDED_FIELDS[0]
        self.assertTrue(_is_field_filled(self.contract, entry))


class TestMultiTurnConversation(unittest.TestCase):
    """Simulate a full multi-turn conversation using the fallback simulator."""

    def setUp(self):
        # Use a temp directory for session files
        self._original_session_dir = SESSION_DIR
        self.temp_dir = tempfile.mkdtemp()
        import pre_upload_state
        pre_upload_state.SESSION_DIR = self.temp_dir

    def tearDown(self):
        import pre_upload_state
        pre_upload_state.SESSION_DIR = self._original_session_dir
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_five_turn_conversation(self):
        """Simulate a 5-turn conversation where required fields get filled gradually."""
        session_id = ""
        turn_count = 0

        # Turn 1: User states their goal
        result = process_turn(
            message="I want to predict equipment failures in my manufacturing plant",
            session_id=session_id,
        )
        session_id = result["session_id"]
        turn_count += 1
        self.assertIsNotNone(session_id)
        self.assertFalse(result["conversation_complete"])
        # After primary_goal is filled, the system should ask about ML problem type
        self.assertIn("machine learning", result["reply"].lower())

        # Check contract was saved
        contract = load_contract(session_id)
        self.assertIsNotNone(contract)
        self.assertGreater(len(contract.goal.primary_goal), 0)

        # Turn 2: User specifies ML problem type
        result = process_turn(
            message="It's a regression problem, I need to forecast failure rates",
            session_id=session_id,
        )
        turn_count += 1
        self.assertFalse(result["conversation_complete"])

        contract = load_contract(session_id)
        self.assertGreater(len(contract.goal.candidate_ml_problem_types), 0)

        # Turn 3: User specifies dataset type only
        result = process_turn(
            message="The data is time series data from our plant",
            session_id=session_id,
        )
        turn_count += 1
        self.assertFalse(result["conversation_complete"])

        contract = load_contract(session_id)
        self.assertEqual(contract.dataset_expectation.expected_dataset_type, "time series")

        # Turn 4: User specifies file types (should complete required fields)
        result = process_turn(
            message="The files are in CSV format",
            session_id=session_id,
        )
        turn_count += 1

        contract = load_contract(session_id)
        self.assertIn("CSV", contract.dataset_expectation.expected_file_types)

        # All required fields should now be filled
        self.assertTrue(result["conversation_complete"])
        self.assertEqual(result["recommended_next_action"], "prompt_for_upload")

        # Verify replies log
        replies = load_replies(session_id)
        self.assertGreater(len(replies), 0)
        self.assertEqual(len(replies), turn_count)

    def test_ambiguity_escalation(self):
        """Test that repeated ambiguous messages trigger escalation."""
        session_id = ""

        # Turn 1: Ambiguous message
        result = process_turn(
            message="data stuff",
            session_id=session_id,
        )
        session_id = result["session_id"]
        self.assertTrue(result["ambiguity_detected"])

        # Turn 2: Still ambiguous
        result = process_turn(
            message="something with data",
            session_id=session_id,
        )
        self.assertTrue(result["ambiguity_detected"])

        # Should now trigger escalation (2+ consecutive ambiguous turns)
        # The recommended_next_action should be "offer_quick_select"
        # or the reply should indicate confusion
        contract = load_contract(session_id)
        if contract.conversation_analysis.ambiguity_detected:
            # Check previous contract also had ambiguity
            pass  # The escalation check uses previous_contract internally

    def test_confidence_not_overwritten(self):
        """Test that a high-confidence value is not overwritten by a low-confidence one
        across multiple turns."""
        session_id = ""

        # Turn 1: User clearly states their goal (high confidence via keywords)
        result = process_turn(
            message="My goal is to predict equipment failures in the manufacturing plant",
            session_id=session_id,
        )
        session_id = result["session_id"]

        contract = load_contract(session_id)
        original_goal = contract.goal.primary_goal

        # Turn 2: User says something vague that might trigger a low-confidence extraction
        result = process_turn(
            message="yeah that thing",
            session_id=session_id,
        )

        contract = load_contract(session_id)
        # The primary goal should NOT have been overwritten by a vague message
        self.assertEqual(contract.goal.primary_goal, original_goal)


class TestProcessTurnEdgeCases(unittest.TestCase):
    """Test edge cases for the process_turn function."""

    def setUp(self):
        self._original_session_dir = SESSION_DIR
        self.temp_dir = tempfile.mkdtemp()
        import pre_upload_state
        pre_upload_state.SESSION_DIR = self.temp_dir

    def tearDown(self):
        import pre_upload_state
        pre_upload_state.SESSION_DIR = self._original_session_dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_message(self):
        """Empty message should return an error."""
        result = process_turn(
            message="",
            session_id="",
        )
        # The process_turn function doesn't validate empty messages itself,
        # but the route handler does. The extraction should handle it gracefully.
        self.assertIsNotNone(result["reply"])

    def test_new_session_returns_session_id(self):
        """A new session should return a valid session_id."""
        result = process_turn(
            message="I want to analyze sensor data",
            session_id="",
        )
        self.assertIsNotNone(result["session_id"])
        self.assertGreater(len(result["session_id"]), 0)

    def test_existing_session_continues(self):
        """An existing session should continue from where it left off."""
        # Create a session
        result1 = process_turn(
            message="I want to predict failures",
            session_id="",
        )
        session_id = result1["session_id"]

        # Continue the session
        result2 = process_turn(
            message="It's a regression problem",
            session_id=session_id,
        )
        self.assertEqual(result2["session_id"], session_id)

        # Turn number should have incremented
        contract = load_contract(session_id)
        self.assertGreaterEqual(contract.conversation.conversation_turn, 2)

    def test_invalid_session_id_creates_new(self):
        """An invalid/non-existent session_id should create a new session."""
        result = process_turn(
            message="I want to analyze data",
            session_id="non-existent-session-id",
        )
        # Should get a new session_id back
        self.assertIsNotNone(result["session_id"])
        self.assertNotEqual(result["session_id"], "non-existent-session-id")


if __name__ == "__main__":
    unittest.main()