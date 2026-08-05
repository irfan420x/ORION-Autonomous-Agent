from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class UserContext(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User-specific preferences and settings")
    recent_commands: List[str] = Field(default_factory=list, description="List of recently executed commands")
    personal_info: Dict[str, Any] = Field(default_factory=dict, description="Anonymized personal information for context")

class WorkspaceContext(BaseModel):
    path: str = Field(..., description="Absolute path to the current workspace directory")
    recent_files: List[str] = Field(default_factory=list, description="List of recently accessed files in the workspace")
    git_status: Optional[Dict[str, Any]] = Field(None, description="Current Git status of the workspace")
    open_windows: List[str] = Field(default_factory=list, description="Titles of open windows related to the workspace")

class ContextBundle(BaseModel):
    current_task_id: Optional[str] = Field(None, description="ID of the currently active task")
    user_context: UserContext = Field(..., description="Context related to the user")
    workspace_context: WorkspaceContext = Field(..., description="Context related to the current workspace")
    chat_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent chat history with the user")
    relevant_documents: List[str] = Field(default_factory=list, description="Summaries or IDs of relevant documents from Knowledge Engine")

class OptimizedContext(BaseModel):
    prompt: str = Field(..., description="The optimized prompt to be sent to the LLM")
    token_count: int = Field(..., description="Estimated token count of the optimized prompt")
    strategy_used: str = Field(..., description="Strategy used for optimization (e.g., sliding_window, RAG)")
