from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

PermissionStatus = Literal["ALLOW", "DENY", "CONFIRM_USER", "CONFIRM_TELEGRAM", "ALLOW_ONCE", "ALLOW_SESSION", "SANDBOX_ONLY"]

class PermissionRequest(BaseModel):
    action: str = Field(..., description="The action for which permission is requested (e.g., 'filesystem.write', 'network.access')")
    agent_id: str = Field(..., description="ID of the agent requesting the permission")
    resource: Optional[str] = Field(None, description="Specific resource involved (e.g., '/etc/passwd', 'https://malicious.com')")
    reason: Optional[str] = Field(None, description="Reason for requesting the permission")

class PermissionResponse(BaseModel):
    request_id: str = Field(..., description="ID of the permission request")
    status: PermissionStatus = Field(..., description="The decision made for the permission request")
    timestamp: float = Field(..., description="Unix timestamp of the decision")
    user_id: Optional[str] = Field(None, description="User ID who made the decision")

class AuditAction(BaseModel):
    action_id: str = Field(..., description="Unique identifier for the audit action")
    timestamp: float = Field(..., description="Unix timestamp of the action")
    agent_id: str = Field(..., description="ID of the agent performing the action")
    action_type: str = Field(..., description="Type of action (e.g., 'file.write', 'command.execute', 'permission.granted')")
    details: Dict[str, Any] = Field({}, description="Detailed payload of the action")
    risk_score: int = Field(0, description="Risk score associated with the action (0-10)")
    user_confirmed: bool = Field(False, description="True if user explicitly confirmed this action")

class SecretInfo(BaseModel):
    key: str = Field(..., description="Key for the secret")
    value_encrypted: str = Field(..., description="Encrypted value of the secret")
    last_accessed: Optional[float] = Field(None, description="Unix timestamp of last access")
    created_at: float = Field(..., description="Unix timestamp of creation")
