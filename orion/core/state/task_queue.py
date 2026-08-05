"""
ORION Task Queue Engine
=======================

Persistent task queue with priority, dependencies, and crash recovery.

Features:
- Add, get, update, and remove tasks
- Priority-based ordering
- Dependency resolution
- JSON file persistence (crash recovery)
- Event publishing on task state changes

Usage:
    tq = TaskQueueEngine(event_bus)
    await tq.start()
    await tq.add_task(task)
    task = await tq.get_next_task()
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from orion.contracts.agent_contracts import Event, Task, TaskID, TaskStatus
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)

# Default persistence file
DEFAULT_STATE_FILE = "state/task_queue.json"


class TaskQueueEngine:
    """
    Persistent task queue with priority and dependency management.
    
    Features:
    - Priority-based task ordering
    - Dependency resolution (tasks wait for dependencies)
    - JSON file persistence for crash recovery
    - Event publishing on task state changes
    """
    
    # Task statuses
    STATUS_PENDING = "PENDING"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"
    
    def __init__(
        self,
        event_bus: EventBus,
        state_file: str = DEFAULT_STATE_FILE,
    ):
        """
        Initialize the Task Queue Engine.
        
        Args:
            event_bus: EventBus for publishing task events.
            state_file: Path to JSON file for persistence.
        """
        self._event_bus = event_bus
        self._state_file = Path(state_file)
        self._tasks: Dict[TaskID, Task] = {}
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_added: int = 0
        self._total_completed: int = 0
        self._total_failed: int = 0
        
        logger.info("TaskQueueEngine initialized (state_file: %s)", state_file)
    
    async def start(self) -> None:
        """Start the task queue and load persisted state."""
        await self.load_state()
        logger.info("TaskQueueEngine started with %d tasks", len(self._tasks))
    
    async def stop(self) -> None:
        """Stop the task queue and persist state."""
        await self.persist_state()
        logger.info("TaskQueueEngine stopped")
    
    async def add_task(self, task: Task) -> None:
        """
        Add a new task to the queue.
        
        Args:
            task: The task to add.
            
        Raises:
            ValueError: If task_id already exists.
        """
        async with self._lock:
            if task.task_id in self._tasks:
                raise ValueError(f"Task '{task.task_id}' already exists")
            
            self._tasks[task.task_id] = task
            self._total_added += 1
            
            # Persist immediately
            await self._persist_internal()
            
            # Publish event
            await self._event_bus.publish(Event(
                event_type="task.added",
                payload={
                    "task_id": task.task_id,
                    "goal": task.goal,
                    "status": task.status,
                },
                timestamp=time.time(),
                source="task_queue",
            ))
            
            logger.info("Task added: %s - %s", task.task_id, task.goal[:50])
    
    async def get_next_task(self) -> Optional[Task]:
        """
        Get the next task to execute based on priority and dependencies.
        
        Returns:
            The next task, or None if no tasks are available.
        """
        async with self._lock:
            # Find tasks that are PENDING and have all dependencies met
            candidates = []
            
            for task in self._tasks.values():
                if task.status != self.STATUS_PENDING:
                    continue
                
                # Check if all dependencies are completed
                if self._are_dependencies_met(task):
                    candidates.append(task)
            
            if not candidates:
                return None
            
            # Sort by created_at (FIFO for now, can add priority later)
            candidates.sort(key=lambda t: t.created_at)
            
            return candidates[0]
    
    async def update_task_status(
        self,
        task_id: TaskID,
        status: TaskStatus,
        reason: str = "",
    ) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: The task to update.
            status: New status.
            reason: Reason for the status change.
            
        Returns:
            True if task was found and updated, False otherwise.
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            old_status = task.status
            task.status = status
            task.updated_at = time.time()
            
            # Update statistics
            if status == self.STATUS_COMPLETED:
                self._total_completed += 1
            elif status == self.STATUS_FAILED:
                self._total_failed += 1
            
            # Persist
            await self._persist_internal()
            
            # Publish event
            await self._event_bus.publish(Event(
                event_type="task.status_changed",
                payload={
                    "task_id": task_id,
                    "old_status": old_status,
                    "new_status": status,
                    "reason": reason,
                },
                timestamp=time.time(),
                source="task_queue",
            ))
            
            logger.info("Task %s: %s -> %s (%s)", task_id, old_status, status, reason)
            return True
    
    async def get_task(self, task_id: TaskID) -> Optional[Task]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: The task ID to look up.
            
        Returns:
            The task, or None if not found.
        """
        return self._tasks.get(task_id)
    
    async def get_all_tasks(self) -> List[Task]:
        """
        Get all tasks in the queue.
        
        Returns:
            List of all tasks.
        """
        return list(self._tasks.values())
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        Get all tasks with a specific status.
        
        Args:
            status: The status to filter by.
            
        Returns:
            List of matching tasks.
        """
        return [t for t in self._tasks.values() if t.status == status]
    
    async def remove_task(self, task_id: TaskID) -> bool:
        """
        Remove a task from the queue.
        
        Args:
            task_id: The task to remove.
            
        Returns:
            True if task was found and removed, False otherwise.
        """
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            del self._tasks[task_id]
            await self._persist_internal()
            
            await self._event_bus.publish(Event(
                event_type="task.removed",
                payload={"task_id": task_id},
                timestamp=time.time(),
                source="task_queue",
            ))
            
            logger.info("Task removed: %s", task_id)
            return True
    
    async def clear_completed(self) -> int:
        """
        Remove all completed tasks.
        
        Returns:
            Number of tasks removed.
        """
        async with self._lock:
            completed = [
                tid for tid, task in self._tasks.items()
                if task.status == self.STATUS_COMPLETED
            ]
            
            for tid in completed:
                del self._tasks[tid]
            
            if completed:
                await self._persist_internal()
                logger.info("Cleared %d completed tasks", len(completed))
            
            return len(completed)
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)
            if not dep_task or dep_task.status != self.STATUS_COMPLETED:
                return False
        return True
    
    async def persist_state(self) -> None:
        """Persist the current state to disk."""
        async with self._lock:
            await self._persist_internal()
    
    async def _persist_internal(self) -> None:
        """Internal persist (must hold lock)."""
        try:
            # Ensure directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert tasks to serializable format
            state = {
                "tasks": {
                    tid: {
                        "task_id": t.task_id,
                        "goal": t.goal,
                        "status": t.status,
                        "dependencies": t.dependencies,
                        "assigned_agent": t.assigned_agent,
                        "created_at": t.created_at,
                        "updated_at": t.updated_at,
                    }
                    for tid, t in self._tasks.items()
                },
                "stats": {
                    "total_added": self._total_added,
                    "total_completed": self._total_completed,
                    "total_failed": self._total_failed,
                },
                "persisted_at": time.time(),
            }
            
            # Write to file
            with open(self._state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.debug("State persisted to %s", self._state_file)
            
        except Exception as e:
            logger.error("Failed to persist state: %s", str(e))
    
    async def load_state(self) -> None:
        """Load state from disk."""
        try:
            if not self._state_file.exists():
                logger.info("No persisted state found at %s", self._state_file)
                return
            
            with open(self._state_file, 'r') as f:
                state = json.load(f)
            
            # Restore tasks
            tasks_data = state.get("tasks", {})
            for tid, t_data in tasks_data.items():
                self._tasks[tid] = Task(**t_data)
            
            # Restore stats
            stats = state.get("stats", {})
            self._total_added = stats.get("total_added", 0)
            self._total_completed = stats.get("total_completed", 0)
            self._total_failed = stats.get("total_failed", 0)
            
            logger.info("Loaded %d tasks from %s", len(self._tasks), self._state_file)
            
        except Exception as e:
            logger.error("Failed to load state: %s", str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get task queue statistics.
        
        Returns:
            Dictionary with statistics.
        """
        status_counts = {}
        for task in self._tasks.values():
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        return {
            "total_tasks": len(self._tasks),
            "status_counts": status_counts,
            "total_added": self._total_added,
            "total_completed": self._total_completed,
            "total_failed": self._total_failed,
            "state_file": str(self._state_file),
        }
