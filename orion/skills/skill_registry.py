"""
ORION Skill System
==================

Reusable workflow system. A Skill is a predefined sequence of steps
that can be executed by agents.

Features:
- Define skills with steps and dependencies
- Execute skills via agents
- Skill registry for discovery
- Parameterized skills

Usage:
    registry = SkillRegistry()
    registry.register(my_skill)
    result = await registry.execute("research_topic", params={"topic": "AI"})
"""

import asyncio
import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class SkillStatus(str, Enum):
    """Status of a skill execution."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SkillStep:
    """A single step in a skill workflow."""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
    ):
        self.step_id = step_id
        self.name = name
        self.action = action
        self.parameters = parameters or {}
        self.dependencies = dependencies or []


class Skill:
    """A reusable workflow with ordered steps."""
    
    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        steps: List[SkillStep],
        version: str = "1.0",
        author: str = "ORION",
        tags: Optional[List[str]] = None,
    ):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.steps = steps
        self.version = version
        self.author = author
        self.tags = tags or []
    
    def get_step(self, step_id: str) -> Optional[SkillStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_execution_order(self) -> List[str]:
        """Get topologically sorted step IDs."""
        # Simple topological sort
        visited = set()
        order = []
        
        def visit(step_id):
            if step_id in visited:
                return
            visited.add(step_id)
            step = self.get_step(step_id)
            if step:
                for dep in step.dependencies:
                    visit(dep)
                order.append(step_id)
        
        for step in self.steps:
            visit(step.step_id)
        
        return order


class SkillExecution:
    """Tracks execution of a skill."""
    
    def __init__(self, skill: Skill, parameters: Dict[str, Any]):
        self.execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        self.skill = skill
        self.parameters = parameters
        self.status = SkillStatus.PENDING
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.step_results: Dict[str, Any] = {}
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "skill_id": self.skill.skill_id,
            "status": self.status.value,
            "parameters": self.parameters,
            "step_results": self.step_results,
            "error": self.error,
        }


class SkillRegistry:
    """Registry for managing and executing skills."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self._event_bus = event_bus
        self._skills: Dict[str, Skill] = {}
        self._executions: Dict[str, SkillExecution] = {}
        self._action_handlers: Dict[str, Callable] = {}
        
        # Stats
        self._total_executions: int = 0
        self._total_succeeded: int = 0
        self._total_failed: int = 0
        
        logger.info("SkillRegistry initialized")
    
    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.skill_id] = skill
        logger.info("Skill registered: %s (%s)", skill.name, skill.skill_id)
    
    def unregister(self, skill_id: str) -> bool:
        """Unregister a skill."""
        if skill_id in self._skills:
            del self._skills[skill_id]
            return True
        return False
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        return self._skills.get(skill_id)
    
    def list_skills(self) -> List[Skill]:
        """List all registered skills."""
        return list(self._skills.values())
    
    def register_action(self, action_name: str, handler: Callable) -> None:
        """Register an action handler for skill steps."""
        self._action_handlers[action_name] = handler
        logger.info("Action handler registered: %s", action_name)
    
    async def execute(
        self,
        skill_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> SkillExecution:
        """
        Execute a skill.
        """
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError(f"Unknown skill: {skill_id}")
        
        execution = SkillExecution(skill, parameters or {})
        self._executions[execution.execution_id] = execution
        self._total_executions += 1
        
        execution.status = SkillStatus.RUNNING
        execution.started_at = time.time()
        
        # Publish start event
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type="skill.started",
                payload=execution.to_dict(),
                timestamp=time.time(),
                source="skill_registry",
            ))
        
        try:
            # Execute steps in order
            order = skill.get_execution_order()
            
            for step_id in order:
                step = skill.get_step(step_id)
                if not step:
                    continue
                
                logger.info("Executing step: %s (%s)", step.name, step.action)
                
                # Merge parameters
                step_params = {**execution.parameters, **step.parameters}
                
                # Execute action
                result = await self._execute_action(step.action, step_params)
                execution.step_results[step_id] = result
            
            execution.status = SkillStatus.COMPLETED
            execution.completed_at = time.time()
            self._total_succeeded += 1
            
            # Publish completion event
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type="skill.completed",
                    payload=execution.to_dict(),
                    timestamp=time.time(),
                    source="skill_registry",
                ))
            
            logger.info("Skill '%s' completed", skill.name)
        
        except Exception as e:
            execution.status = SkillStatus.FAILED
            execution.error = str(e)
            execution.completed_at = time.time()
            self._total_failed += 1
            
            logger.error("Skill '%s' failed: %s", skill.name, e)
            
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type="skill.failed",
                    payload=execution.to_dict(),
                    timestamp=time.time(),
                    source="skill_registry",
                ))
        
        return execution
    
    async def _execute_action(self, action: str, parameters: Dict[str, Any]) -> Any:
        """Execute a skill action."""
        handler = self._action_handlers.get(action)
        
        if handler:
            if asyncio.iscoroutinefunction(handler):
                return await handler(**parameters)
            else:
                return handler(**parameters)
        
        # Default: return acknowledgment
        return f"Action '{action}' executed with params: {parameters}"
    
    def get_execution(self, execution_id: str) -> Optional[SkillExecution]:
        """Get an execution by ID."""
        return self._executions.get(execution_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "registered_skills": len(self._skills),
            "total_executions": self._total_executions,
            "succeeded": self._total_succeeded,
            "failed": self._total_failed,
            "action_handlers": list(self._action_handlers.keys()),
        }
