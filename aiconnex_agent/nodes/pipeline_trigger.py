"""
aiconnex_agent/nodes/pipeline_trigger.py - Node 6: Pipeline Trigger (Stub)
"""
from aiconnex_agent.state import AgentState

def pipeline_trigger_node(state: AgentState) -> AgentState:
    state["stage"] = "pipeline_triggered"
    return state
