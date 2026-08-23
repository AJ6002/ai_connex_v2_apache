"""
Agent SPEC Contract - Agentic Studio SPEC and runtime capability contract.
"""


from pydantic import BaseModel, Field


class AgentSPECContract(BaseModel):
    agent_id: str = Field(..., description="Unique agent SPEC ID")
    agent_name: str = Field(..., description="Agent name (e.g. Jane, DiagnosticAgent)")
    allowed_capabilities: list[str] = Field(default_factory=list, description="Allow-listed capabilities")
    autonomy_level: str = Field(default="HITL", description="HITL, AUTO, BOUNDED")
    system_prompt_version: str = Field(default="v1.0", description="System prompt version")
    model_name: str = Field(default="Qwen2.5-Coder", description="Underlying LLM model tag")
