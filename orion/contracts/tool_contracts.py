from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

class ToolArgument(BaseModel):
    name: str = Field(..., description="Name of the argument")
    type: Literal["string", "integer", "boolean", "array", "object"] = Field(..., description="Data type of the argument")
    description: Optional[str] = Field(None, description="Description of the argument")
    required: bool = Field(False, description="Whether the argument is required")
    default: Optional[Any] = Field(None, description="Default value for the argument")

class ToolDefinition(BaseModel):
    tool_id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Human-readable name of the tool")
    description: str = Field(..., description="Detailed description of what the tool does")
    version: str = Field("1.0", description="Version of the tool")
    type: Literal["cli", "python_function", "api"] = Field(..., description="Type of the tool")
    command: Optional[str] = Field(None, description="CLI command or Python function path")
    args_schema: List[ToolArgument] = Field(default_factory=list, description="Schema defining the arguments for the tool")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities this tool provides (e.g., 'filesystem.read', 'network.scan')")
    permissions_required: List[str] = Field(default_factory=list, description="List of specific permissions this tool requires")
    health_check_command: Optional[str] = Field(None, description="Command to check if the tool is installed and working")

class ToolExecutionRequest(BaseModel):
    tool_id: str = Field(..., description="ID of the tool to execute")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool execution")

class ToolExecutionResult(BaseModel):
    tool_id: str = Field(..., description="ID of the executed tool")
    success: bool = Field(..., description="True if the tool executed successfully")
    output: Optional[str] = Field(None, description="Standard output from the tool")
    error: Optional[str] = Field(None, description="Standard error from the tool")
    return_code: Optional[int] = Field(None, description="Return code of the tool execution")
    parsed_output: Optional[Dict[str, Any]] = Field(None, description="Structured, parsed output if available")
