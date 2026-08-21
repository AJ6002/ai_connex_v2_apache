"""
Tenant Context Contract - Multi-tenant identity, security, and quota context.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field

class TenantContract(BaseModel):
    tenant_id: str = Field(..., description="Unique tenant organization ID")
    tenant_name: str = Field(..., description="Human readable organization name")
    user_id: str = Field(..., description="Authenticated user identifier")
    roles: List[str] = Field(default_factory=lambda: ["operator"], description="Assigned user roles")
    site_scope: List[str] = Field(default_factory=list, description="Authorized site IDs")
    asset_scope: List[str] = Field(default_factory=list, description="Authorized asset IDs")
    quotas: Dict[str, Any] = Field(default_factory=dict, description="Resource limits (max_gb, max_concurrent_jobs)")
    policy_version: str = Field(default="v1.0", description="Security policy version")
    is_active: bool = Field(default=True, description="Tenant active status")
