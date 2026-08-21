"""
Audit Contract - Security event log and compliance trail contract.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class AuditContract(BaseModel):
    audit_id: str = Field(..., description="Unique audit event ID")
    tenant_uid: str = Field(..., description="Tenant organization ID")
    user_uid: str = Field(..., description="User ID associated with event")
    action: str = Field(..., description="Executed action name")
    resource_type: str = Field(..., description="Resource class affected (dataset, model, deployment, agent)")
    resource_id: str = Field(..., description="Resource ID affected")
    status: str = Field(default="SUCCESS", description="SUCCESS, DENIED, FAILED")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed audit context")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
