"""
aiconnex_agent/nodes/data_explorer.py - Node 4: Data Explorer (Stub)
"""
from aiconnex_agent.state import AgentState

def data_explorer_node(state: AgentState) -> AgentState:
    state["stage"] = "data_explored"
    return state
