# tests/test_memory_builder.py
import pytest
from aiconnex_agent.memory.events import make_event
from aiconnex_agent.memory.policy_engine import MemoryPolicyEngine
from aiconnex_agent.memory.memory_builder import MemoryBuilder


def _fixture_log():
    return [
        make_event("ConversationParsed", "wf_1", "parser", "conversation", "wf_1", {"intent": "train_rul"}),
        make_event("PlanCreated", "wf_1", "planner", "plan", "wf_1", {"steps": 3}),
        make_event("DatasetCompiled", "wf_1", "scout", "dataset", "ds_nasa_fd001", {"rows": 26898}),
        make_event("ClarificationAnswered", "wf_1", "clarification", "decision", "wf_1", {"question": "mode?", "answer": "auto"}),
        make_event("ArchiveUploaded", "wf_1", "scout", "conversation", "wf_1", {}, outcome="failure"),
    ]


def test_dataset_compiled_lands_in_entities():
    builder = MemoryBuilder(MemoryPolicyEngine())
    bank = builder.build(_fixture_log())
    assert "ds_nasa_fd001" in bank.entities
    assert bank.entities["ds_nasa_fd001"].observations[0]["rows"] == 26898


def test_clarification_answered_lands_in_decisions():
    builder = MemoryBuilder(MemoryPolicyEngine())
    bank = builder.build(_fixture_log())
    assert len(bank.decisions) == 1
    assert bank.decisions[0].answer == "auto"


def test_conversation_parsed_lands_in_session():
    builder = MemoryBuilder(MemoryPolicyEngine())
    bank = builder.build(_fixture_log())
    assert "wf_1" in bank.session
    assert "ConversationParsed" in bank.session["wf_1"].steps_run
    assert "PlanCreated" in bank.session["wf_1"].steps_run


def test_failure_event_lands_in_procedures():
    builder = MemoryBuilder(MemoryPolicyEngine())
    bank = builder.build(_fixture_log())
    assert len(bank.procedures) == 1
    assert bank.procedures[0].pattern == "ArchiveUploaded"
    assert bank.procedures[0].outcome == "failure"
    assert bank.procedures[0].occurrences == 1


def test_duplicate_failure_patterns_are_aggregated_not_duplicated():
    log = [
        make_event("ArchiveUploaded", "wf_1", "scout", "conversation", "wf_1", {}, outcome="failure"),
        make_event("ArchiveUploaded", "wf_2", "scout", "conversation", "wf_2", {}, outcome="failure"),
    ]
    builder = MemoryBuilder(MemoryPolicyEngine())
    bank = builder.build(log)
    assert len(bank.procedures) == 1
    assert bank.procedures[0].occurrences == 2


def test_build_is_idempotent():
    builder = MemoryBuilder(MemoryPolicyEngine())
    log = _fixture_log()
    bank1 = builder.build(log)
    bank2 = builder.build(log)
    assert bank1.to_context() == bank2.to_context()


def test_discarded_event_types_are_dropped():
    log = [make_event("ClarificationRequested", "wf_1", "clarification", "decision", "wf_1", {})]
    builder = MemoryBuilder(MemoryPolicyEngine())
    bank = builder.build(log)
    assert bank.decisions == []
    assert bank.entities == {}
