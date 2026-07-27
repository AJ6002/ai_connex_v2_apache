"""
aiconnex_agent/nodes/scope_narrower.py - Node 5: Scope Narrower (Stub)
"""
from aiconnex_agent.state import AgentState

def scope_narrower_node(state: AgentState) -> AgentState:
    state["stage"] = "scope_narrowed"
    return state
