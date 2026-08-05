from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from orion.contracts.observability_contracts import LogEntry
from orion.contracts.planning_contracts import TaskGraph

class DebugCommand(BaseModel):
    command: str = Field(..., description="The debug command to execute")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the debug command")

class DebugCommandResult(BaseModel):
    success: bool = Field(..., description="True if the command executed successfully")
    output: str = Field(..., description="Output from the debug command")
    error: Optional[str] = Field(None, description="Error message if command failed")

class MemorySnapshot(BaseModel):
    session_memory: Dict[str, Any] = Field(default_factory=dict, description="Snapshot of session memory content")
    working_memory_summary: str = Field(..., description="Summary of working memory")
    long_term_memory_stats: Dict[str, Any] = Field(default_factory=dict, description="Statistics about long-term memory")
    semantic_memory_stats: Dict[str, Any] = Field(default_factory=dict, description="Statistics about semantic memory")

class WorkflowVisualization(BaseModel):
    graph_data: Dict[str, Any] = Field(..., description="Data for visualizing the workflow graph (e.g., DOT format, JSON)")
    highlighted_tasks: List[str] = Field(default_factory=list, description="List of task IDs to highlight")

class PromptTemplate(BaseModel):
    template_id: str = Field(..., description="Unique ID for the prompt template")
    name: str = Field(..., description="Name of the prompt template")
    content: str = Field(..., description="The actual prompt template string")
    variables: List[str] = Field(default_factory=list, description="List of variables used in the template")
    description: Optional[str] = Field(None, description="Description of the template's purpose")
