"""
DAG Contract - Computational strategy definition contract.
"""


from pydantic import BaseModel, Field


class DAGContract(BaseModel):
    dag_id: str = Field(..., description="Unique DAG strategy identifier (e.g. DAG_514)")
    dag_name: str = Field(..., description="Human readable strategy name")
    description: str = Field(..., description="Computational strategy summary")
    nodes: list[str] = Field(default_factory=list, description="Ordered pipeline node IDs")
    edges: list[dict[str, str]] = Field(default_factory=list, description="Directed dependencies between nodes")
    required_inputs: list[str] = Field(default_factory=list, description="Required input feature types")
    output_target: str = Field(..., description="Output target classification")
