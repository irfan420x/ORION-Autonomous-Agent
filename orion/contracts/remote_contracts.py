from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class TelegramUpdate(BaseModel):
    update_id: int = Field(..., description="The update’s unique identifier.")
    message_id: Optional[int] = Field(None, description="Unique message identifier inside this chat.")
    chat_id: Optional[int] = Field(None, description="Unique identifier for the target chat.")
    from_user_id: Optional[int] = Field(None, description="Unique identifier for the user who sent the message.")
    text: Optional[str] = Field(None, description="Text of the message.")
    command: Optional[str] = Field(None, description="Command extracted from the message (e.g., /status).")

class TelegramResponse(BaseModel):
    chat_id: int = Field(..., description="Unique identifier for the target chat.")
    text: str = Field(..., description="Text of the message to be sent.")
    parse_mode: Optional[str] = Field("MarkdownV2", description="Parse mode for text (e.g., MarkdownV2, HTML).")

class APIRequest(BaseModel):
    method: str = Field(..., description="HTTP method (e.g., GET, POST).")
    path: str = Field(..., description="Request path.")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers.")
    body: Optional[Dict[str, Any]] = Field(None, description="Request body.")
    auth_token: Optional[str] = Field(None, description="Authentication token.")

class APIResponse(BaseModel):
    status_code: int = Field(..., description="HTTP status code.")
    headers: Dict[str, str] = Field(default_factory=dict, description="Response headers.")
    body: Optional[Dict[str, Any]] = Field(None, description="Response body.")

class RemoteCommand(BaseModel):
    command_id: str = Field(..., description="Unique identifier for the remote command.")
    command_type: str = Field(..., description="Type of command (e.g., 'execute_task', 'get_status').")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Command-specific payload.")
    source: Literal["telegram", "api", "websocket"] = Field(..., description="Source of the command.")
    user_id: Optional[str] = Field(None, description="User ID who issued the command.")

class WebSocketMessage(BaseModel):
    message_type: str = Field(..., description="Type of WebSocket message (e.g., 'event', 'command', 'status').")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload.")
    timestamp: float = Field(..., description="Unix timestamp of the message.")
