"""
Tests for ORION Planning Engine (M3.2)
=======================================
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from orion.core.communication.event_bus import EventBus
from orion.core.state.task_queue import TaskQueueEngine
from orion.intelligence.llm_client import LLMClient, LLMResponse
from orion.intelligence.planning_engine import PlanningEngine, Goal, GoalStatus


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def llm_client():
    client = MagicMock(spec=LLMClient)
    client.chat = AsyncMock()
    return client


@pytest.fixture
def task_queue(event_bus):
    return TaskQueueEngine(event_bus, state_file="/tmp/test_plan_queue.json")


@pytest.fixture
def planner(event_bus, llm_client, task_queue):
    return PlanningEngine(event_bus, llm_client, task_queue)


@pytest.fixture
def planner_no_llm(event_bus):
    return PlanningEngine(event_bus)


# ── Goal Tests ───────────────────────────────────────────────

class TestGoal:
    def test_goal_creation(self):
        goal = Goal("g1", "Test goal")
        assert goal.goal_id == "g1"
        assert goal.description == "Test goal"
        assert goal.status == GoalStatus.PENDING

    def test_goal_to_dict(self):
        goal = Goal("g1", "Test goal")
        d = goal.to_dict()
        assert d["goal_id"] == "g1"
        assert d["status"] == "PENDING"


# ── Planning Engine Tests ────────────────────────────────────

class TestPlanningEngine:
    def test_initial_state(self, planner):
        stats = planner.get_stats()
        assert stats["total_goals"] == 0
        assert stats["llm_available"] is True

    def test_initial_state_no_llm(self, planner_no_llm):
        stats = planner_no_llm.get_stats()
        assert stats["llm_available"] is False

    @pytest.mark.asyncio
    async def test_plan_with_llm(self, planner, llm_client):
        """Plan with LLM decomposition."""
        # Mock LLM response
        llm_response = LLMResponse(
            content=json.dumps([
                {"goal": "Research topic", "dependencies": []},
                {"goal": "Write summary", "dependencies": [1]},
                {"goal": "Review and edit", "dependencies": [2]},
            ]),
            model="xiaomi/mimo-v2.5-pro",
            tokens_input=50,
            tokens_output=100,
        )
        llm_client.chat.return_value = llm_response
        
        goal = await planner.plan("Research and summarize AI trends")
        
        assert goal.status in (GoalStatus.PENDING, GoalStatus.EXECUTING)
        assert len(goal.tasks) == 3
        assert planner._total_goals == 1

    @pytest.mark.asyncio
    async def test_plan_heuristic_fallback(self, planner_no_llm):
        """Plan without LLM uses heuristic."""
        goal = await planner_no_llm.plan("Simple task")
        
        assert goal.status == GoalStatus.PENDING
        assert len(goal.tasks) == 1  # Single task heuristic

    @pytest.mark.asyncio
    async def test_plan_auto_execute(self, planner, llm_client):
        """Plan with auto_execute adds tasks to queue."""
        llm_response = LLMResponse(
            content=json.dumps([
                {"goal": "Step 1", "dependencies": []},
                {"goal": "Step 2", "dependencies": [1]},
            ]),
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        goal = await planner.plan("Test goal", auto_execute=True)
        
        assert goal.status == GoalStatus.EXECUTING
        assert len(goal.tasks) == 2

    @pytest.mark.asyncio
    async def test_plan_publishes_events(self, event_bus, planner_no_llm):
        """Planning publishes events."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("intelligence.planning.started", handler)
        await event_bus.subscribe("intelligence.planning.completed", handler)
        
        await planner_no_llm.plan("Test")
        
        assert len(events) == 2
        assert events[0].event_type == "intelligence.planning.started"
        assert events[1].event_type == "intelligence.planning.completed"

    @pytest.mark.asyncio
    async def test_plan_llm_failure_fallback(self, planner, llm_client):
        """LLM failure falls back to heuristic."""
        llm_client.chat.side_effect = RuntimeError("LLM unavailable")
        
        goal = await planner.plan("Test goal")
        
        # Should still succeed with heuristic
        assert len(goal.tasks) == 1

    def test_get_goal(self, planner_no_llm):
        """Can get a goal by ID."""
        goal = Goal("g1", "Test")
        planner_no_llm._goals["g1"] = goal
        
        assert planner_no_llm.get_goal("g1") == goal
        assert planner_no_llm.get_goal("nonexistent") is None

    def test_get_all_goals(self, planner_no_llm):
        """Can get all goals."""
        planner_no_llm._goals["g1"] = Goal("g1", "A")
        planner_no_llm._goals["g2"] = Goal("g2", "B")
        
        assert len(planner_no_llm.get_all_goals()) == 2

    def test_get_active_goals(self, planner_no_llm):
        """Active goals filter works."""
        planner_no_llm._goals["g1"] = Goal("g1", "A", GoalStatus.PENDING)
        planner_no_llm._goals["g2"] = Goal("g2", "B", GoalStatus.COMPLETED)
        planner_no_llm._goals["g3"] = Goal("g3", "C", GoalStatus.EXECUTING)
        
        active = planner_no_llm.get_active_goals()
        assert len(active) == 2

    @pytest.mark.asyncio
    async def test_complete_goal(self, planner_no_llm):
        """Can complete a goal."""
        goal = Goal("g1", "Test")
        planner_no_llm._goals["g1"] = goal
        
        result = await planner_no_llm.complete_goal("g1")
        
        assert result is True
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_nonexistent(self, planner_no_llm):
        """Completing nonexistent goal returns False."""
        result = await planner_no_llm.complete_goal("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_goal(self, planner_no_llm):
        """Can cancel a goal."""
        goal = Goal("g1", "Test")
        planner_no_llm._goals["g1"] = goal
        
        result = await planner_no_llm.cancel_goal("g1")
        
        assert result is True
        assert goal.status == GoalStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_stats(self, planner_no_llm):
        """Stats are tracked."""
        await planner_no_llm.plan("Goal 1")
        await planner_no_llm.plan("Goal 2")
        
        stats = planner_no_llm.get_stats()
        assert stats["total_goals"] == 2
        assert stats["total_tasks_created"] == 2


# ── LLM Decomposition Tests ─────────────────────────────────

class TestLLMDecomposition:
    @pytest.mark.asyncio
    async def test_parse_valid_json(self, planner, llm_client):
        """Valid JSON response is parsed correctly."""
        llm_response = LLMResponse(
            content=json.dumps([
                {"goal": "A", "dependencies": []},
                {"goal": "B", "dependencies": [1]},
            ]),
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        goal = await planner.plan("Test")
        assert len(goal.tasks) == 2

    @pytest.mark.asyncio
    async def test_parse_json_with_text(self, planner, llm_client):
        """JSON embedded in text is extracted."""
        llm_response = LLMResponse(
            content='Here is the plan:\n[{"goal": "A", "dependencies": []}]\nDone.',
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        goal = await planner.plan("Test")
        assert len(goal.tasks) == 1

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, planner, llm_client):
        """Invalid JSON falls back to heuristic."""
        llm_response = LLMResponse(
            content="This is not JSON at all",
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        goal = await planner.plan("Test")
        # Should fallback to heuristic (single task)
        assert len(goal.tasks) == 1


# ── GoalStatus Tests ─────────────────────────────────────────

class TestGoalStatus:
    def test_all_statuses(self):
        assert GoalStatus.PENDING == "PENDING"
        assert GoalStatus.PLANNING == "PLANNING"
        assert GoalStatus.EXECUTING == "EXECUTING"
        assert GoalStatus.COMPLETED == "COMPLETED"
        assert GoalStatus.FAILED == "FAILED"
        assert GoalStatus.CANCELLED == "CANCELLED"
