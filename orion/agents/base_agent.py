"""
ORION Base Agent
================

Foundation for all ORION agents. Provides:
- Registration with AgentRegistry
- Heartbeat publishing
- Event subscription
- Task execution interface

All specialized agents inherit from BaseAgent.
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from orion.contracts.agent_contracts import (
    AgentCapability,
    AgentHeartbeat,
    AgentID,
    AgentRegistration,
    Event,
    Task,
    TaskStatus,
)
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all ORION agents.
    
    Provides common functionality:
    - Event Bus integration
    - Heartbeat publishing
    - Task execution interface
    - Lifecycle management (start/stop)
    """
    
    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        capabilities: Optional[List[str]] = None,
        heartbeat_interval: float = 5.0,
    ):
        self.agent_id = AgentID(agent_id)
        self._event_bus = event_bus
        self._capabilities = capabilities or []
        self._heartbeat_interval = heartbeat_interval
        
        # State
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._start_time: float = 0.0
        
        # Stats
        self._tasks_executed: int = 0
        self._tasks_succeeded: int = 0
        self._tasks_failed: int = 0
        self._events_received: int = 0
        
        logger.info("Agent '%s' created", agent_id)
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def uptime(self) -> float:
        return time.time() - self._start_time if self._start_time else 0.0
    
    async def start(self) -> None:
        """Start the agent: register, subscribe, start heartbeat."""
        if self._running:
            logger.warning("Agent '%s' already running", self.agent_id)
            return
        
        self._running = True
        self._start_time = time.time()
        
        # Register with EventBus
        await self._register()
        
        # Subscribe to events
        await self._subscribe_events()
        
        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("Agent '%s' started", self.agent_id)
    
    async def stop(self) -> None:
        """Stop the agent gracefully."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop heartbeat
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Publish stop event
        await self._event_bus.publish(Event(
            event_type="agent.stopped",
            payload={"agent_id": str(self.agent_id)},
            timestamp=time.time(),
            source=str(self.agent_id),
        ))
        
        logger.info("Agent '%s' stopped", self.agent_id)
    
    async def _register(self) -> None:
        """Register the agent with the EventBus."""
        capabilities = [
            AgentCapability(name=cap) for cap in self._capabilities
        ]
        
        registration = AgentRegistration(
            agent_id=self.agent_id,
            capabilities=capabilities,
            health_status="HEALTHY",
            endpoint=f"agent://{self.agent_id}",
        )
        
        await self._event_bus.publish(Event(
            event_type="agent.registered",
            payload=registration.model_dump(),
            timestamp=time.time(),
            source=str(self.agent_id),
        ))
        
        logger.info("Agent '%s' registered with capabilities: %s", 
                    self.agent_id, self._capabilities)
    
    async def _subscribe_events(self) -> None:
        """Subscribe to relevant events. Override in subclasses."""
        # Subscribe to task assignments
        await self._event_bus.subscribe(
            f"task.assigned.{self.agent_id}",
            self._handle_task_assigned
        )
    
    async def _handle_task_assigned(self, event: Event) -> None:
        """Handle a task assignment event."""
        task_data = event.payload.get("task")
        if not task_data:
            return
        
        task = Task(**task_data)
        logger.info("Agent '%s' received task: %s", self.agent_id, task.goal)
        
        try:
            result = await self.execute_task(task)
            self._tasks_succeeded += 1
            
            # Publish task completed event
            await self._event_bus.publish(Event(
                event_type="task.completed",
                payload={
                    "task_id": str(task.task_id),
                    "agent_id": str(self.agent_id),
                    "result": result,
                },
                timestamp=time.time(),
                source=str(self.agent_id),
            ))
        except Exception as e:
            self._tasks_failed += 1
            logger.error("Agent '%s' task failed: %s", self.agent_id, e)
            
            await self._event_bus.publish(Event(
                event_type="task.failed",
                payload={
                    "task_id": str(task.task_id),
                    "agent_id": str(self.agent_id),
                    "error": str(e),
                },
                timestamp=time.time(),
                source=str(self.agent_id),
            ))
        finally:
            self._tasks_executed += 1
    
    @abstractmethod
    async def execute_task(self, task: Task) -> Any:
        """
        Execute a task. Must be implemented by subclasses.
        
        Args:
            task: The task to execute
            
        Returns:
            Result of the task execution
        """
        pass
    
    async def _heartbeat_loop(self) -> None:
        """Publish heartbeat periodically."""
        while self._running:
            try:
                heartbeat = AgentHeartbeat(
                    agent_id=self.agent_id,
                    timestamp=time.time(),
                    load_avg=[0.0, 0.0, 0.0],
                    memory_usage_percent=0.0,
                )
                
                await self._event_bus.publish(Event(
                    event_type="agent.heartbeat",
                    payload=heartbeat.model_dump(),
                    timestamp=time.time(),
                    source=str(self.agent_id),
                ))
                
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat error for '%s': %s", self.agent_id, e)
                await asyncio.sleep(self._heartbeat_interval)
    
    async def handle_event(self, event: Event) -> None:
        """Handle an incoming event. Override in subclasses for custom handling."""
        self._events_received += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "agent_id": str(self.agent_id),
            "running": self._running,
            "capabilities": self._capabilities,
            "uptime_seconds": round(self.uptime, 1),
            "tasks_executed": self._tasks_executed,
            "tasks_succeeded": self._tasks_succeeded,
            "tasks_failed": self._tasks_failed,
            "events_received": self._events_received,
        }
