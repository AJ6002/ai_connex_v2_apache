"""
Recipe Contract - Parameterized step-by-step execution recipe contract.
"""

from typing import Any

from pydantic import BaseModel, Field


class RecipeStep(BaseModel):
    step_id: str = Field(..., description="Step identifier")
    operation: str = Field(..., description="Primitive operation name")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Step arguments and parameters")

class RecipeContract(BaseModel):
    recipe_id: str = Field(..., description="Unique recipe version ID")
    recipe_name: str = Field(..., description="Human readable recipe title")
    domain: str = Field(default="industrial_telemetry", description="Industrial domain classification")
    target_task: str = Field(..., description="Target task type (e.g. regression_rul, anomaly_detection)")
    steps: list[RecipeStep] = Field(default_factory=list, description="Ordered execution steps")
    version: str = Field(default="v1.0", description="Recipe version")
