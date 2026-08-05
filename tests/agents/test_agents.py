"""
Tests for ORION Agent System (M4.1)
====================================
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from orion.core.communication.event_bus import EventBus
from orion.contracts.agent_contracts import Event, Task, TaskID
from orion.agents.base_agent import BaseAgent
from orion.agents.orchestrator_agent import OrchestratorAgent
from orion.agents.executor_agent import ExecutorAgent


@pytest.fixture
def event_bus():
    return EventBus()


# ── Base Agent Tests ─────────────────────────────────────────

class ConcreteAgent(BaseAgent):
    """Concrete implementation for testing."""
    
    async def execute_task(self, task):
        return f"Executed: {task.goal}"


class TestBaseAgent:
    @pytest.mark.asyncio
    async def test_creation(self, event_bus):
        agent = ConcreteAgent("test_agent", event_bus, ["test_cap"])
        assert str(agent.agent_id) == "test_agent"
        assert not agent.is_running

    @pytest.mark.asyncio
    async def test_start_stop(self, event_bus):
        agent = ConcreteAgent("test_agent", event_bus)
        await agent.start()
        assert agent.is_running
        
        await agent.stop()
        assert not agent.is_running

    @pytest.mark.asyncio
    async def test_capabilities(self, event_bus):
        agent = ConcreteAgent("test", event_bus, ["cap1", "cap2"])
        assert agent._capabilities == ["cap1", "cap2"]

    @pytest.mark.asyncio
    async def test_stats(self, event_bus):
        agent = ConcreteAgent("test", event_bus)
        stats = agent.get_stats()
        
        assert stats["agent_id"] == "test"
        assert stats["tasks_executed"] == 0

    @pytest.mark.asyncio
    async def test_execute_task(self, event_bus):
        agent = ConcreteAgent("test", event_bus)
        task = Task(
            task_id=TaskID("t1"),
            goal="Test task",
            created_at=time.time(),
            updated_at=time.time(),
        )
        result = await agent.execute_task(task)
        assert "Executed" in result

    @pytest.mark.asyncio
    async def test_heartbeat_publishes(self, event_bus):
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("agent.heartbeat", handler)
        
        agent = ConcreteAgent("test", event_bus, heartbeat_interval=0.1)
        await agent.start()
        await asyncio.sleep(0.3)
        await agent.stop()
        
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_registration_event(self, event_bus):
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("agent.registered", handler)
        
        agent = ConcreteAgent("test", event_bus, ["cap1"])
        await agent.start()
        await agent.stop()
        
        assert len(events) == 1


# ── Orchestrator Agent Tests ─────────────────────────────────

class TestOrchestratorAgent:
    @pytest.mark.asyncio
    async def test_creation(self, event_bus):
        agent = OrchestratorAgent(event_bus)
        assert str(agent.agent_id) == "orchestrator"
        assert "coordinate" in agent._capabilities

    @pytest.mark.asyncio
    async def test_start_stop(self, event_bus):
        agent = OrchestratorAgent(event_bus)
        await agent.start()
        assert agent.is_running
        await agent.stop()

    @pytest.mark.asyncio
    async def test_handle_user_goal(self, event_bus):
        agent = OrchestratorAgent(event_bus)
        await agent.start()
        
        # Directly call the handler instead of publishing
        event = Event(
            event_type="user.goal",
            payload={"goal": "Test goal", "user_id": 123},
            timestamp=time.time(),
            source="test",
        )
        await agent._handle_user_goal(event)
        
        await agent.stop()

    @pytest.mark.asyncio
    async def test_execute_task(self, event_bus):
        agent = OrchestratorAgent(event_bus)
        task = Task(
            task_id=TaskID("t1"),
            goal="Test",
            created_at=time.time(),
            updated_at=time.time(),
        )
        result = await agent.execute_task(task)
        assert "delegates" in result.lower()


# ── Executor Agent Tests ─────────────────────────────────────

class TestExecutorAgent:
    @pytest.mark.asyncio
    async def test_creation(self, event_bus):
        agent = ExecutorAgent(event_bus)
        assert str(agent.agent_id) == "executor"
        assert "execute" in agent._capabilities

    @pytest.mark.asyncio
    async def test_start_stop(self, event_bus):
        agent = ExecutorAgent(event_bus)
        await agent.start()
        assert agent.is_running
        await agent.stop()

    @pytest.mark.asyncio
    async def test_execute_date_task(self, event_bus):
        agent = ExecutorAgent(event_bus)
        task = Task(
            task_id=TaskID("t1"),
            goal="What is the current date?",
            created_at=time.time(),
            updated_at=time.time(),
        )
        result = await agent.execute_task(task)
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_disk_task(self, event_bus):
        agent = ExecutorAgent(event_bus)
        task = Task(
            task_id=TaskID("t1"),
            goal="Check disk space",
            created_at=time.time(),
            updated_at=time.time(),
        )
        result = await agent.execute_task(task)
        assert "%" in result or "Filesystem" in result

    @pytest.mark.asyncio
    async def test_unsafe_command_blocked(self, event_bus):
        agent = ExecutorAgent(event_bus)
        result = await agent._run_command("rm -rf /")
        assert "not allowed" in result.lower()

    @pytest.mark.asyncio
    async def test_safe_command_runs(self, event_bus):
        agent = ExecutorAgent(event_bus)
        result = await agent._run_command("echo hello")
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_stats(self, event_bus):
        agent = ExecutorAgent(event_bus)
        stats = agent.get_stats()
        assert stats["agent_id"] == "executor"
