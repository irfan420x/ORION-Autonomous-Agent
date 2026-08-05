from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from orion.contracts.agent_contracts import Task, TaskID

class StructuredGoal(BaseModel):
    goal_id: str = Field(..., description="Unique identifier for the structured goal")
    description: str = Field(..., description="Detailed description of the goal")
    priority: int = Field(5, description="Priority level of the goal (1-10, 10 being highest)")
    constraints: List[str] = Field([], description="List of constraints for achieving the goal")
    success_criteria: List[str] = Field([], description="Criteria for determining goal success")

class TaskGraphNode(BaseModel):
    task: Task = Field(..., description="The task represented by this node")
    dependencies: List[TaskID] = Field([], description="List of TaskIDs that must be completed before this task")

class TaskGraph(BaseModel):
    graph_id: str = Field(..., description="Unique identifier for the task graph")
    goal_id: str = Field(..., description="ID of the structured goal this graph is for")
    nodes: Dict[TaskID, TaskGraphNode] = Field(..., description="Dictionary of tasks in the graph, keyed by TaskID")
    edges: Dict[TaskID, List[TaskID]] = Field(..., description="Adjacency list representing dependencies (key: task, value: tasks it depends on)")

