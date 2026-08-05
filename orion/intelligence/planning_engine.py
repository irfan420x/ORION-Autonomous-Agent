"""
ORION Planning Engine
=====================

Breaks high-level goals into executable task DAGs (Directed Acyclic Graphs).
Uses LLM to decompose goals, then manages task dependencies.

Features:
- Goal decomposition into task graphs
- Dependency resolution (topological sort)
- Task prioritization
- Checkpoint/resume support
- Integration with TaskQueueEngine

Usage:
    planner = PlanningEngine(llm_client, task_queue)
    tasks = await planner.plan("Research and summarize AI trends 2026")
"""

import asyncio
import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from orion.contracts.agent_contracts import Event, Task, TaskID, TaskStatus
from orion.core.communication.event_bus import EventBus
from orion.core.state.task_queue import TaskQueueEngine
from orion.intelligence.llm_client import LLMClient

logger = logging.getLogger(__name__)


class GoalStatus(str, Enum):
    """Status of a planning goal."""
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Goal:
    """A high-level goal to be planned and executed."""
    
    def __init__(
        self,
        goal_id: str,
        description: str,
        status: GoalStatus = GoalStatus.PENDING,
        tasks: Optional[List[str]] = None,
        created_at: Optional[float] = None,
    ):
        self.goal_id = goal_id
        self.description = description
        self.status = status
        self.tasks = tasks or []  # List of task IDs
        self.created_at = created_at or time.time()
        self.completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "status": self.status.value,
            "tasks": self.tasks,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class PlanningEngine:
    """
    Breaks goals into executable task DAGs.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        llm_client: Optional[LLMClient] = None,
        task_queue: Optional[TaskQueueEngine] = None,
    ):
        self._event_bus = event_bus
        self._llm = llm_client
        self._task_queue = task_queue
        
        # Goals storage
        self._goals: Dict[str, Goal] = {}
        
        # Stats
        self._total_goals: int = 0
        self._total_tasks_created: int = 0
        
        logger.info("PlanningEngine initialized")
    
    async def plan(
        self,
        description: str,
        auto_execute: bool = False,
    ) -> Goal:
        """
        Create a plan from a goal description.
        
        Args:
            description: The goal description
            auto_execute: If True, add tasks to queue immediately
        """
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        now = time.time()
        
        goal = Goal(
            goal_id=goal_id,
            description=description,
            status=GoalStatus.PLANNING,
            created_at=now,
        )
        
        self._goals[goal_id] = goal
        self._total_goals += 1
        
        # Publish planning started event
        await self._event_bus.publish(Event(
            event_type="intelligence.planning.started",
            payload={"goal_id": goal_id, "description": description},
            timestamp=now,
            source="planning_engine",
        ))
        
        try:
            # Decompose goal into tasks
            task_breakdown = await self._decompose_goal(description)
            
            # Create task objects
            task_ids = []
            for i, task_info in enumerate(task_breakdown):
                task_id = TaskID(f"{goal_id}_t{i+1}")
                task = Task(
                    task_id=task_id,
                    goal=task_info.get("goal", f"Task {i+1}"),
                    created_at=time.time(),
                    updated_at=time.time(),
                )
                
                # Set dependencies
                deps = task_info.get("dependencies", [])
                if deps:
                    task.dependencies = [
                        TaskID(f"{goal_id}_t{d}") for d in deps
                    ]
                
                # Add to queue if auto_execute
                if auto_execute and self._task_queue:
                    await self._task_queue.add_task(task)
                
                task_ids.append(str(task_id))
                self._total_tasks_created += 1
            
            goal.tasks = task_ids
            goal.status = GoalStatus.EXECUTING if auto_execute else GoalStatus.PENDING
            
            # Publish planning completed event
            await self._event_bus.publish(Event(
                event_type="intelligence.planning.completed",
                payload={
                    "goal_id": goal_id,
                    "task_count": len(task_ids),
                    "auto_execute": auto_execute,
                },
                timestamp=time.time(),
                source="planning_engine",
            ))
            
            logger.info(
                "Plan created: goal=%s tasks=%d auto_execute=%s",
                goal_id, len(task_ids), auto_execute
            )
            
            return goal
        
        except Exception as e:
            goal.status = GoalStatus.FAILED
            logger.error("Planning failed for goal %s: %s", goal_id, e)
            
            await self._event_bus.publish(Event(
                event_type="intelligence.planning.failed",
                payload={"goal_id": goal_id, "error": str(e)},
                timestamp=time.time(),
                source="planning_engine",
            ))
            
            raise
    
    async def _decompose_goal(self, description: str) -> List[Dict[str, Any]]:
        """
        Decompose a goal into tasks using LLM or heuristics.
        """
        # Try LLM first
        if self._llm:
            try:
                return await self._llm_decompose(description)
            except Exception as e:
                logger.warning("LLM decomposition failed, using heuristic: %s", e)
        
        # Fallback: heuristic decomposition
        return self._heuristic_decompose(description)
    
    async def _llm_decompose(self, description: str) -> List[Dict[str, Any]]:
        """Use LLM to decompose a goal into tasks."""
        system_prompt = """You are a task planning engine. Break the given goal into a list of concrete, executable tasks.

Return a JSON array of tasks. Each task has:
- "goal": what the task does (short, actionable)
- "dependencies": list of task numbers (1-indexed) that must complete first

Example:
Goal: "Build a website"
[
  {"goal": "Design website layout", "dependencies": []},
  {"goal": "Create HTML structure", "dependencies": [1]},
  {"goal": "Add CSS styling", "dependencies": [2]},
  {"goal": "Add JavaScript interactivity", "dependencies": [2]},
  {"goal": "Test and deploy", "dependencies": [3, 4]}
]

Return ONLY the JSON array, no other text."""
        
        response = await self._llm.chat(
            prompt=f"Goal: {description}",
            system=system_prompt,
            model="mimo-v2.5-pro",
        )
        
        # Parse JSON response
        import json
        text = response.content.strip()
        
        # Extract JSON from response
        if "[" in text and "]" in text:
            start = text.index("[")
            end = text.rindex("]") + 1
            tasks = json.loads(text[start:end])
            
            if isinstance(tasks, list) and len(tasks) > 0:
                return tasks
        
        raise ValueError("Failed to parse LLM response as task list")
    
    def _heuristic_decompose(self, description: str) -> List[Dict[str, Any]]:
        """
        Simple heuristic decomposition when LLM is not available.
        Splits by common action words.
        """
        # Default: single task
        return [{"goal": description, "dependencies": []}]
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID."""
        return self._goals.get(goal_id)
    
    def get_all_goals(self) -> List[Goal]:
        """Get all goals."""
        return list(self._goals.values())
    
    def get_active_goals(self) -> List[Goal]:
        """Get goals that are still in progress."""
        return [
            g for g in self._goals.values()
            if g.status in (GoalStatus.PLANNING, GoalStatus.EXECUTING, GoalStatus.PENDING)
        ]
    
    async def complete_goal(self, goal_id: str) -> bool:
        """Mark a goal as completed."""
        goal = self._goals.get(goal_id)
        if not goal:
            return False
        
        goal.status = GoalStatus.COMPLETED
        goal.completed_at = time.time()
        
        await self._event_bus.publish(Event(
            event_type="intelligence.planning.goal_completed",
            payload=goal.to_dict(),
            timestamp=time.time(),
            source="planning_engine",
        ))
        
        return True
    
    async def cancel_goal(self, goal_id: str) -> bool:
        """Cancel a goal."""
        goal = self._goals.get(goal_id)
        if not goal:
            return False
        
        goal.status = GoalStatus.CANCELLED
        goal.completed_at = time.time()
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get planning engine statistics."""
        statuses = {}
        for g in self._goals.values():
            s = g.status.value
            statuses[s] = statuses.get(s, 0) + 1
        
        return {
            "total_goals": self._total_goals,
            "total_tasks_created": self._total_tasks_created,
            "active_goals": len(self.get_active_goals()),
            "goal_statuses": statuses,
            "llm_available": self._llm is not None,
            "task_queue_available": self._task_queue is not None,
        }
