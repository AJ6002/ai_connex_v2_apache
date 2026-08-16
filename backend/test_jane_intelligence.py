"""
test_jane_intelligence.py — Jane AI Operations Assistant Intelligence Test Suite
==================================================================================
Runs 4 comprehensive intelligence test scenarios:
1. Operational Tool Calling (Pipeline Status & Telemetry).
2. Hybrid Dense+Sparse RAG Context Retrieval & Grounding.
3. Uncertainty Protocol Adherence ("I don't have enough data...").
4. SQLite Sliding Window Dialogue Continuity.
"""

from __future__ import annotations

import os
import sys
import json

# Ensure core directory is on path
sys.path.insert(0, os.path.dirname(__file__))

from jane_assistant import run_jane_assistant, save_chat_turn, get_chat_history, hybrid_retriever

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  TEST SCENARIO: {title}")
    print("=" * 70)

def test_tool_calling():
    print_header("1. Operational Tool Calling & Structured Actions")
    session_id = "test_intel_tool_call"
    query = "Check pipeline status for run run_99"
    
    res = run_jane_assistant(session_id=session_id, user_input=query)
    print(f"User Query : {query}")
    print(f"Jane Reply : {res['reply']}")
    print(f"Tools Exec : {json.dumps(res['tools_executed'], indent=2)}")
    
    assert len(res['tools_executed']) > 0, "Tool calling should execute a tool"
    print("[PASS] Tool Calling Test Successful!")

def test_rag_grounding():
    print_header("2. Hybrid RAG Retrieval & Context Grounding")
    session_id = "test_intel_rag"
    query = "What endpoints does the API Gateway expose?"
    
    res = run_jane_assistant(session_id=session_id, user_input=query)
    print(f"User Query : {query}")
    print(f"Jane Reply : {res['reply']}")
    print(f"RAG Context: {res['rag_context_used']}")
    
    assert "antigravity" in res['rag_context_used'].lower() or "api" in res['rag_context_used'].lower(), "RAG context should be retrieved"
    print("[PASS] RAG Retrieval Grounding Test Successful!")

def test_uncertainty_protocol():
    print_header("3. Uncertainty Protocol Adherence (No Hallucination)")
    session_id = "test_intel_uncertainty"
    query = "What is the secret quantum key for project unknown_xyz?"
    
    res = run_jane_assistant(session_id=session_id, user_input=query)
    print(f"User Query : {query}")
    print(f"Jane Reply : {res['reply']}")
    
    expected_phrase = "I don't have enough data in the current AI-Connex records to answer that accurately."
    assert expected_phrase.lower() in res['reply'].lower(), "Uncertainty protocol phrase must be triggered"
    print("[PASS] Uncertainty Protocol Test Successful!")

def test_sqlite_memory_continuity():
    print_header("4. SQLite Dialogue Memory Sliding Window Continuity")
    session_id = "test_intel_memory_seq"
    
    # Turn 1
    run_jane_assistant(session_id=session_id, user_input="Hello Jane, my project is SolarPowerPredictor")
    
    # Check SQLite store
    history = get_chat_history(session_id=session_id, limit=5)
    print(f"Recorded Session Memory ({len(history)} turns):")
    for turn in history:
        print(f"  [{turn['role'].upper()}]: {turn['content']}")
        
    assert len(history) >= 2, "Chat history should store both user and assistant turns"
    print("[PASS] SQLite Session Memory Test Successful!")

if __name__ == "__main__":
    print("\n[START] STARTING JANE ASSISTANT INTELLIGENCE EVALUATION SUITE...")
    try:
        test_tool_calling()
        test_rag_grounding()
        test_uncertainty_protocol()
        test_sqlite_memory_continuity()
        print("\n[SUCCESS] ALL 4 INTELLIGENCE TEST SCENARIOS PASSED 100% SUCCESSFULLY!\n")
    except Exception as err:
        print(f"\n[FAIL] TEST FAILED: {err}\n")
