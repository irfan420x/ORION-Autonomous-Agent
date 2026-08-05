"""
ORION Orchestrator Agent
========================

High-level agent that coordinates all other agents.
Receives user goals, initiates planning, and oversees execution.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event, Task, TaskID
from orion.core.communication.event_bus import EventBus
from orion.agents.base_agent import BaseAgent
from orion.intelligence.planning_engine import PlanningEngine

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Top-level coordinator agent.
    
    Responsibilities:
    - Receive user goals (from Telegram, voice, etc.)
    - Initiate planning via PlanningEngine
    - Assign tasks to appropriate agents
    - Monitor execution progress
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        planning_engine: Optional[PlanningEngine] = None,
    ):
        super().__init__(
            agent_id="orchestrator",
            event_bus=event_bus,
            capabilities=["coordinate", "plan", "assign"],
        )
        self._planner = planning_engine
        self._active_goals: Dict[str, Any] = {}
    
    async def _subscribe_events(self) -> None:
        """Subscribe to goal and task events."""
        await super()._subscribe_events()
        
        # Listen for user goals
        await self._event_bus.subscribe("user.goal", self._handle_user_goal)
        
        # Listen for task completions
        await self._event_bus.subscribe("task.completed", self._handle_task_completed)
        await self._event_bus.subscribe("task.failed", self._handle_task_failed)
    
    async def _handle_user_goal(self, event: Event) -> None:
        """Handle a user goal submission."""
        goal_desc = event.payload.get("goal", "")
        user_id = event.payload.get("user_id")
        
        logger.info("Orchestrator received goal: %s", goal_desc)
        
        if self._planner:
            # Use PlanningEngine to decompose goal
            goal = await self._planner.plan(goal_desc, auto_execute=False)
            self._active_goals[goal.goal_id] = goal
            
            # Assign tasks to agents
            await self._assign_tasks(goal)
        else:
            # Simple single-task execution
            await self._create_simple_task(goal_desc)
    
    async def _assign_tasks(self, goal) -> None:
        """Assign planned tasks to appropriate agents."""
        for task_id in goal.tasks:
            # For now, assign all tasks to executor
            await self._event_bus.publish(Event(
                event_type=f"task.assigned.executor",
                payload={
                    "task": {
                        "task_id": task_id,
                        "goal": goal.description,
                        "status": "PENDING",
                        "created_at": time.time(),
                        "updated_at": time.time(),
                    }
                },
                timestamp=time.time(),
                source="orchestrator",
            ))
            
            logger.info("Assigned task %s to executor", task_id)
    
    async def _create_simple_task(self, description: str) -> None:
        """Create a simple task when no planner is available."""
        task_id = TaskID(f"task_{int(time.time())}")
        
        await self._event_bus.publish(Event(
            event_type="task.assigned.executor",
            payload={
                "task": {
                    "task_id": str(task_id),
                    "goal": description,
                    "status": "PENDING",
                    "created_at": time.time(),
                    "updated_at": time.time(),
                }
            },
            timestamp=time.time(),
            source="orchestrator",
        ))
    
    async def _handle_task_completed(self, event: Event) -> None:
        """Handle task completion."""
        task_id = event.payload.get("task_id")
        agent_id = event.payload.get("agent_id")
        logger.info("Task %s completed by %s", task_id, agent_id)
    
    async def _handle_task_failed(self, event: Event) -> None:
        """Handle task failure."""
        task_id = event.payload.get("task_id")
        error = event.payload.get("error")
        logger.warning("Task %s failed: %s", task_id, error)
    
    async def execute_task(self, task: Task) -> Any:
        """Orchestrator doesn't execute tasks directly."""
        return "Orchestrator delegates tasks to other agents"
