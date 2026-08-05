"""
Unit Tests for ORION State Machine and Task Queue
=================================================

Tests cover:
- StateMachine: transitions, callbacks, guards, history
- TaskQueueEngine: add, get, update, persist, load, crash recovery
"""

import asyncio
import json
import os
import pytest
import tempfile
import time

from orion.contracts.agent_contracts import Event, Task
from orion.core.communication.event_bus import EventBus
from orion.core.state.state_machine import StateMachine, State
from orion.core.state.task_queue import TaskQueueEngine


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def event_bus():
    """Create a fresh EventBus."""
    return EventBus(max_history=100)


@pytest.fixture
def state_machine(event_bus):
    """Create a fresh StateMachine."""
    return StateMachine(event_bus, initial_state=State.IDLE)


@pytest.fixture
def temp_state_file():
    """Create a temporary file for task queue persistence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def task_queue(event_bus, temp_state_file):
    """Create a fresh TaskQueueEngine."""
    return TaskQueueEngine(event_bus, state_file=temp_state_file)


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        task_id="task_001",
        goal="Test task",
        status="PENDING",
        dependencies=[],
        created_at=time.time(),
        updated_at=time.time(),
    )


# ============================================================================
# StateMachine Tests
# ============================================================================

class TestStateMachine:
    """Tests for the StateMachine class."""
    
    @pytest.mark.asyncio
    async def test_initial_state(self, state_machine):
        """Test that initial state is set correctly."""
        assert state_machine.current_state == State.IDLE
    
    @pytest.mark.asyncio
    async def test_valid_transition(self, state_machine):
        """Test valid state transition."""
        result = await state_machine.transition_to(State.PROCESSING, reason="Starting work")
        assert result is True
        assert state_machine.current_state == State.PROCESSING
    
    @pytest.mark.asyncio
    async def test_invalid_transition(self, state_machine):
        """Test invalid state transition."""
        # IDLE -> SHUTDOWN is valid, but IDLE -> PAUSED is not
        result = await state_machine.transition_to(State.PAUSED)
        assert result is False
        assert state_machine.current_state == State.IDLE
    
    @pytest.mark.asyncio
    async def test_transition_history(self, state_machine):
        """Test that transitions are recorded in history."""
        await state_machine.transition_to(State.PROCESSING, reason="Start")
        await state_machine.transition_to(State.IDLE, reason="Done")
        
        history = state_machine.history
        assert len(history) == 2
        assert history[0].from_state == State.IDLE
        assert history[0].to_state == State.PROCESSING
        assert history[1].from_state == State.PROCESSING
        assert history[1].to_state == State.IDLE
    
    @pytest.mark.asyncio
    async def test_enter_callback(self, state_machine):
        """Test enter state callback."""
        entered = []
        
        async def on_enter():
            entered.append(True)
        
        state_machine.on_enter(State.PROCESSING, on_enter)
        await state_machine.transition_to(State.PROCESSING)
        
        assert len(entered) == 1
    
    @pytest.mark.asyncio
    async def test_exit_callback(self, state_machine):
        """Test exit state callback."""
        exited = []
        
        async def on_exit():
            exited.append(True)
        
        state_machine.on_exit(State.IDLE, on_exit)
        await state_machine.transition_to(State.PROCESSING)
        
        assert len(exited) == 1
    
    @pytest.mark.asyncio
    async def test_valid_transitions_list(self, state_machine):
        """Test getting valid transitions from current state."""
        valid = state_machine.get_valid_transitions()
        assert State.PROCESSING in valid
        assert State.SHUTDOWN in valid
        assert State.PAUSED not in valid
    
    @pytest.mark.asyncio
    async def test_stats(self, state_machine):
        """Test statistics."""
        await state_machine.transition_to(State.PROCESSING)
        
        stats = state_machine.get_stats()
        assert stats["current_state"] == "PROCESSING"
        assert stats["total_transitions"] == 1
    
    @pytest.mark.asyncio
    async def test_event_published(self, event_bus, state_machine):
        """Test that state changes publish events."""
        received = []
        
        async def handler(event: Event):
            received.append(event)
        
        await event_bus.subscribe("state.changed", handler)
        await state_machine.transition_to(State.PROCESSING)
        
        assert len(received) == 1
        assert received[0].payload["to_state"] == "PROCESSING"


# ============================================================================
# TaskQueueEngine Tests
# ============================================================================

class TestTaskQueueEngine:
    """Tests for the TaskQueueEngine class."""
    
    @pytest.mark.asyncio
    async def test_add_task(self, task_queue, sample_task):
        """Test adding a task."""
        await task_queue.add_task(sample_task)
        
        task = await task_queue.get_task("task_001")
        assert task is not None
        assert task.goal == "Test task"
    
    @pytest.mark.asyncio
    async def test_add_duplicate_task(self, task_queue, sample_task):
        """Test that adding a duplicate task raises ValueError."""
        await task_queue.add_task(sample_task)
        
        with pytest.raises(ValueError, match="already exists"):
            await task_queue.add_task(sample_task)
    
    @pytest.mark.asyncio
    async def test_get_next_task(self, task_queue):
        """Test getting the next task (FIFO)."""
        task_1 = Task(task_id="t1", goal="First", status="PENDING", created_at=1.0, updated_at=1.0)
        task_2 = Task(task_id="t2", goal="Second", status="PENDING", created_at=2.0, updated_at=2.0)
        
        await task_queue.add_task(task_1)
        await task_queue.add_task(task_2)
        
        next_task = await task_queue.get_next_task()
        assert next_task.task_id == "t1"
    
    @pytest.mark.asyncio
    async def test_get_next_task_with_dependencies(self, task_queue):
        """Test that tasks with unmet dependencies are skipped."""
        task_1 = Task(task_id="t1", goal="Dependency", status="PENDING", created_at=1.0, updated_at=1.0)
        task_2 = Task(task_id="t2", goal="Dependent", status="PENDING", dependencies=["t1"], created_at=2.0, updated_at=2.0)
        
        await task_queue.add_task(task_1)
        await task_queue.add_task(task_2)
        
        # task_2 depends on task_1, so task_1 should come first
        next_task = await task_queue.get_next_task()
        assert next_task.task_id == "t1"
        
        # Complete task_1
        await task_queue.update_task_status("t1", "COMPLETED")
        
        # Now task_2 should be available
        next_task = await task_queue.get_next_task()
        assert next_task.task_id == "t2"
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, task_queue, sample_task):
        """Test updating task status."""
        await task_queue.add_task(sample_task)
        
        success = await task_queue.update_task_status("task_001", "COMPLETED", "Done")
        assert success is True
        
        task = await task_queue.get_task("task_001")
        assert task.status == "COMPLETED"
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, task_queue):
        """Test updating a task that doesn't exist."""
        success = await task_queue.update_task_status("nonexistent", "COMPLETED")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_remove_task(self, task_queue, sample_task):
        """Test removing a task."""
        await task_queue.add_task(sample_task)
        
        success = await task_queue.remove_task("task_001")
        assert success is True
        
        task = await task_queue.get_task("task_001")
        assert task is None
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, task_queue):
        """Test filtering tasks by status."""
        task_1 = Task(task_id="t1", goal="Pending", status="PENDING", created_at=1.0, updated_at=1.0)
        task_2 = Task(task_id="t2", goal="Done", status="COMPLETED", created_at=2.0, updated_at=2.0)
        
        await task_queue.add_task(task_1)
        await task_queue.add_task(task_2)
        
        pending = await task_queue.get_tasks_by_status("PENDING")
        assert len(pending) == 1
        assert pending[0].task_id == "t1"
    
    @pytest.mark.asyncio
    async def test_clear_completed(self, task_queue):
        """Test clearing completed tasks."""
        task_1 = Task(task_id="t1", goal="Done", status="COMPLETED", created_at=1.0, updated_at=1.0)
        task_2 = Task(task_id="t2", goal="Pending", status="PENDING", created_at=2.0, updated_at=2.0)
        
        await task_queue.add_task(task_1)
        await task_queue.add_task(task_2)
        
        count = await task_queue.clear_completed()
        assert count == 1
        
        tasks = await task_queue.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].task_id == "t2"
    
    @pytest.mark.asyncio
    async def test_persistence(self, event_bus, temp_state_file, sample_task):
        """Test that tasks persist to disk."""
        # Create and add task
        queue_1 = TaskQueueEngine(event_bus, state_file=temp_state_file)
        await queue_1.add_task(sample_task)
        await queue_1.persist_state()
        
        # Create new queue and load
        queue_2 = TaskQueueEngine(event_bus, state_file=temp_state_file)
        await queue_2.load_state()
        
        task = await queue_2.get_task("task_001")
        assert task is not None
        assert task.goal == "Test task"
    
    @pytest.mark.asyncio
    async def test_crash_recovery(self, event_bus, temp_state_file):
        """Test that tasks survive simulated crash."""
        # Add tasks
        queue_1 = TaskQueueEngine(event_bus, state_file=temp_state_file)
        await queue_1.add_task(Task(
            task_id="t1", goal="Survive crash", status="IN_PROGRESS",
            created_at=time.time(), updated_at=time.time(),
        ))
        await queue_1.persist_state()
        
        # Simulate crash - create new queue
        queue_2 = TaskQueueEngine(event_bus, state_file=temp_state_file)
        await queue_2.start()
        
        task = await queue_2.get_task("t1")
        assert task is not None
        assert task.status == "IN_PROGRESS"  # Status preserved
    
    @pytest.mark.asyncio
    async def test_stats(self, task_queue, sample_task):
        """Test statistics."""
        await task_queue.add_task(sample_task)
        await task_queue.update_task_status("task_001", "COMPLETED")
        
        stats = task_queue.get_stats()
        assert stats["total_tasks"] == 1
        assert stats["total_completed"] == 1
    
    @pytest.mark.asyncio
    async def test_event_published(self, event_bus, task_queue, sample_task):
        """Test that task operations publish events."""
        received = []
        
        async def handler(event: Event):
            received.append(event)
        
        await event_bus.subscribe("task.*", handler)
        await task_queue.add_task(sample_task)
        
        assert len(received) == 1
        assert received[0].event_type == "task.added"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Tests for StateMachine + TaskQueue working together."""
    
    @pytest.mark.asyncio
    async def test_state_transition_on_task_start(self, event_bus, state_machine, task_queue):
        """Test that state changes when task starts."""
        # Add task
        task = Task(task_id="t1", goal="Test", status="PENDING", created_at=time.time(), updated_at=time.time())
        await task_queue.add_task(task)
        
        # Transition to PROCESSING
        await state_machine.transition_to(State.PROCESSING, reason="Starting task t1")
        
        # Get and start task
        next_task = await task_queue.get_next_task()
        assert next_task is not None
        
        await task_queue.update_task_status(next_task.task_id, "IN_PROGRESS")
        
        # Complete task
        await task_queue.update_task_status(next_task.task_id, "COMPLETED")
        
        # Transition back to IDLE
        await state_machine.transition_to(State.IDLE, reason="Task completed")
        
        assert state_machine.current_state == State.IDLE
        assert len(state_machine.history) == 2
