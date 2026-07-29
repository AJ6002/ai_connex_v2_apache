# tests/test_planning_intent_mapper.py
import pytest
from aiconnex_agent.planning.intent_plan_mapper import IntentPlanMapper


def test_compile_zip_plan():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("compile_zip")
    assert steps[0]["target_agent"] == "scout"
    assert steps[-1]["target_agent"] == "memory"


def test_train_rul_plan_includes_platform():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("train_rul")
    agents = [s["target_agent"] for s in steps]
    assert agents == ["scout", "platform", "memory"]


def test_detect_anomalies_plan_includes_platform():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("detect_anomalies")
    agents = [s["target_agent"] for s in steps]
    assert agents == ["scout", "platform", "memory"]


def test_query_status_plan_is_memory_only():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("query_status")
    assert len(steps) == 1
    assert steps[0]["target_agent"] == "memory"


def test_unknown_intent_falls_back_to_scout_discovery():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("general")
    assert len(steps) == 1
    assert steps[0]["target_agent"] == "scout"

    steps_unknown = mapper.get_plan("totally_made_up_intent")
    assert steps_unknown[0]["target_agent"] == "scout"


def test_step_ids_are_unique_and_sequential():
    mapper = IntentPlanMapper()
    steps = mapper.get_plan("train_rul")
    ids = [s["step_id"] for s in steps]
    assert ids == ["step_1", "step_2", "step_3"]
