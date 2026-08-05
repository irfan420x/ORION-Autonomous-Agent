"""
Tests for ORION Skill System (M4.2)
====================================
"""

import asyncio
import pytest
import time

from orion.core.communication.event_bus import EventBus
from orion.skills.skill_registry import (
    Skill, SkillStep, SkillRegistry, SkillExecution, SkillStatus
)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def registry(event_bus):
    return SkillRegistry(event_bus)


@pytest.fixture
def sample_skill():
    steps = [
        SkillStep("s1", "Step 1", "action_a"),
        SkillStep("s2", "Step 2", "action_b", dependencies=["s1"]),
        SkillStep("s3", "Step 3", "action_c", dependencies=["s1"]),
    ]
    return Skill(
        skill_id="test_skill",
        name="Test Skill",
        description="A test skill",
        steps=steps,
        tags=["test"],
    )


# ── Skill Tests ──────────────────────────────────────────────

class TestSkill:
    def test_creation(self, sample_skill):
        assert sample_skill.skill_id == "test_skill"
        assert sample_skill.name == "Test Skill"
        assert len(sample_skill.steps) == 3

    def test_get_step(self, sample_skill):
        step = sample_skill.get_step("s1")
        assert step is not None
        assert step.name == "Step 1"

    def test_get_step_not_found(self, sample_skill):
        assert sample_skill.get_step("nonexistent") is None

    def test_get_execution_order(self, sample_skill):
        order = sample_skill.get_execution_order()
        assert order[0] == "s1"  # s1 has no dependencies
        assert "s2" in order
        assert "s3" in order
        assert order.index("s1") < order.index("s2")
        assert order.index("s1") < order.index("s3")


class TestSkillStep:
    def test_creation(self):
        step = SkillStep("s1", "Test", "action")
        assert step.step_id == "s1"
        assert step.parameters == {}

    def test_with_parameters(self):
        step = SkillStep("s1", "Test", "action", parameters={"key": "value"})
        assert step.parameters["key"] == "value"

    def test_with_dependencies(self):
        step = SkillStep("s1", "Test", "action", dependencies=["s0"])
        assert "s0" in step.dependencies


# ── SkillExecution Tests ─────────────────────────────────────

class TestSkillExecution:
    def test_creation(self, sample_skill):
        execution = SkillExecution(sample_skill, {"param": "value"})
        assert execution.status == SkillStatus.PENDING
        assert execution.skill == sample_skill

    def test_to_dict(self, sample_skill):
        execution = SkillExecution(sample_skill, {})
        d = execution.to_dict()
        assert "execution_id" in d
        assert d["status"] == "PENDING"


# ── SkillRegistry Tests ──────────────────────────────────────

class TestSkillRegistry:
    def test_initial_state(self, registry):
        assert len(registry.list_skills()) == 0

    def test_register_skill(self, registry, sample_skill):
        registry.register(sample_skill)
        assert len(registry.list_skills()) == 1
        assert registry.get_skill("test_skill") == sample_skill

    def test_unregister_skill(self, registry, sample_skill):
        registry.register(sample_skill)
        assert registry.unregister("test_skill") is True
        assert len(registry.list_skills()) == 0

    def test_unregister_nonexistent(self, registry):
        assert registry.unregister("nonexistent") is False

    def test_get_skill(self, registry, sample_skill):
        registry.register(sample_skill)
        assert registry.get_skill("test_skill") is not None
        assert registry.get_skill("nonexistent") is None

    def test_list_skills(self, registry, sample_skill):
        registry.register(sample_skill)
        skills = registry.list_skills()
        assert len(skills) == 1

    @pytest.mark.asyncio
    async def test_execute_skill(self, registry, sample_skill):
        registry.register(sample_skill)
        
        execution = await registry.execute("test_skill", {"param": "value"})
        
        assert execution.status == SkillStatus.COMPLETED
        assert len(execution.step_results) == 3

    @pytest.mark.asyncio
    async def test_execute_nonexistent(self, registry):
        with pytest.raises(ValueError, match="Unknown skill"):
            await registry.execute("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_with_action_handler(self, registry, sample_skill):
        results = []
        
        async def my_action(**kwargs):
            results.append(kwargs)
            return "done"
        
        registry.register_action("action_a", my_action)
        registry.register(sample_skill)
        
        await registry.execute("test_skill")
        
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_execute_publishes_events(self, event_bus, registry, sample_skill):
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("skill.started", handler)
        await event_bus.subscribe("skill.completed", handler)
        
        registry.register(sample_skill)
        await registry.execute("test_skill")
        
        assert len(events) == 2
        assert events[0].event_type == "skill.started"
        assert events[1].event_type == "skill.completed"

    @pytest.mark.asyncio
    async def test_execute_failed_skill(self, registry):
        """Skill with failing action handler."""
        steps = [SkillStep("s1", "Fail", "bad_action")]
        skill = Skill("fail", "Fail Skill", "Fails", steps)
        
        async def bad_action(**kwargs):
            raise RuntimeError("Action failed")
        
        registry.register_action("bad_action", bad_action)
        registry.register(skill)
        
        execution = await registry.execute("fail")
        
        assert execution.status == SkillStatus.FAILED
        assert execution.error is not None

    def test_register_action(self, registry):
        def my_action():
            pass
        
        registry.register_action("test", my_action)
        assert "test" in registry._action_handlers

    def test_get_execution(self, registry, sample_skill):
        execution = SkillExecution(sample_skill, {})
        registry._executions[execution.execution_id] = execution
        
        assert registry.get_execution(execution.execution_id) is not None

    def test_stats(self, registry, sample_skill):
        registry.register(sample_skill)
        stats = registry.get_stats()
        
        assert stats["registered_skills"] == 1
        assert stats["total_executions"] == 0


# ── SkillStatus Tests ────────────────────────────────────────

class TestSkillStatus:
    def test_all_statuses(self):
        assert SkillStatus.PENDING == "PENDING"
        assert SkillStatus.RUNNING == "RUNNING"
        assert SkillStatus.COMPLETED == "COMPLETED"
        assert SkillStatus.FAILED == "FAILED"
        assert SkillStatus.CANCELLED == "CANCELLED"
