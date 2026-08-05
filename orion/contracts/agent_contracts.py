from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


# Use simple string type aliases instead of custom classes
# This is more compatible with Pydantic v2
AgentID = str
TaskID = str
TaskStatus = str


class AgentCapability(BaseModel):
    name: str = Field(..., description="Name of the capability, e.g., 'can_browse', 'can_code'")
    version: str = Field("1.0", description="Version of the capability")
    description: Optional[str] = Field(None, description="Description of the capability")


class AgentRegistration(BaseModel):
    agent_id: AgentID = Field(..., description="Unique identifier for the agent")
    capabilities: List[AgentCapability] = Field(..., description="List of capabilities the agent possesses")
    health_status: str = Field("HEALTHY", description="Current health status of the agent")
    endpoint: Optional[str] = Field(None, description="Endpoint for direct communication if applicable")


class AgentHeartbeat(BaseModel):
    agent_id: AgentID = Field(..., description="Unique identifier for the agent sending the heartbeat")
    timestamp: float = Field(..., description="Unix timestamp of the heartbeat")
    load_avg: List[float] = Field(..., description="System load average (1, 5, 15 min)")
    memory_usage_percent: float = Field(..., description="Percentage of memory used")


class Event(BaseModel):
    event_type: str = Field(..., description="Type of the event, e.g., 'agent.heartbeat', 'task.created'")
    payload: Dict[str, Any] = Field(..., description="Event-specific data")
    timestamp: float = Field(..., description="Unix timestamp of when the event occurred")
    source: AgentID = Field(..., description="Agent or module that originated the event")


class Task(BaseModel):
    task_id: TaskID = Field(..., description="Unique identifier for the task")
    goal: str = Field(..., description="High-level goal of the task")
    status: TaskStatus = Field("PENDING", description="Current status of the task")
    dependencies: List[TaskID] = Field([], description="List of task IDs this task depends on")
    assigned_agent: Optional[AgentID] = Field(None, description="Agent currently assigned to this task")
    created_at: float = Field(..., description="Unix timestamp of task creation")
    updated_at: float = Field(..., description="Unix timestamp of last update")
