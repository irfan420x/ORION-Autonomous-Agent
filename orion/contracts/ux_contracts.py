from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

NotificationType = Literal["info", "warning", "error", "success", "confirmation"]

class Notification(BaseModel):
    notification_id: str = Field(..., description="Unique identifier for the notification")
    title: str = Field(..., description="Title of the notification")
    message: str = Field(..., description="Content of the notification")
    type: NotificationType = Field("info", description="Type of notification")
    timestamp: float = Field(..., description="Unix timestamp of when the notification was created")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="List of actionable buttons or links in the notification")

class ConfirmationRequest(BaseModel):
    request_id: str = Field(..., description="Unique identifier for the confirmation request")
    prompt: str = Field(..., description="The question or statement requiring user confirmation")
    timeout: int = Field(60, description="Timeout in seconds for user response")

class ConfirmationResponse(BaseModel):
    request_id: str = Field(..., description="ID of the confirmation request")
    confirmed: bool = Field(..., description="True if user confirmed, False otherwise")
    timestamp: float = Field(..., description="Unix timestamp of user response")

class UIElementState(BaseModel):
    element_id: str = Field(..., description="Unique identifier for the UI element")
    visibility: bool = Field(..., description="True if the element is visible")
    enabled: bool = Field(..., description="True if the element is enabled for interaction")
    text: Optional[str] = Field(None, description="Current text content of the element")

class OrbState(BaseModel):
    state: Literal["idle", "listening", "thinking", "speaking", "alert", "busy"] = Field(..., description="Current state of the Floating Orb")
    animation_name: Optional[str] = Field(None, description="Name of the animation to play")
    color: Optional[str] = Field(None, description="Color of the orb (e.g., hex code)")
