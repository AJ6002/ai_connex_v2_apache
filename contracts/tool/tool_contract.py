"""
Tool Contract - Tool Gateway capability contract.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

class ToolContract(BaseModel):
    tool_id: str = Field(..., description="Unique tool identifier")
    capability_name: str = Field(..., description="Capability method name")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for inputs")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for outputs")
    risk_class: str = Field(default="LOW", description="LOW, MEDIUM, HIGH, CRITICAL")
    requires_approval: bool = Field(default=False, description="Whether human approval is required before execution")
