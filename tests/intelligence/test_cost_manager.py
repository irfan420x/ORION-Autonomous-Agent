"""
Tests for ORION Cost Manager (M3.4)
====================================
"""

import asyncio
import pytest
import time
from unittest.mock import MagicMock

from orion.core.communication.event_bus import EventBus
from orion.intelligence.llm_client import LLMClient, LLMResponse, ModelConfig
from orion.intelligence.model_router import ModelRouter
from orion.intelligence.cost_manager import CostManager


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def llm_client():
    client = LLMClient(default_model="mimo-v2.5-pro")
    return client


@pytest.fixture
def router(llm_client):
    return ModelRouter(llm_client)


@pytest.fixture
def manager(event_bus, llm_client, router):
    return CostManager(event_bus, llm_client, router, monthly_budget=50.0)


@pytest.fixture
def manager_no_llm(event_bus):
    return CostManager(event_bus, monthly_budget=50.0)


# ── Cost Manager Tests ───────────────────────────────────────

class TestCostManager:
    def test_initial_state(self, manager):
        stats = manager.get_stats()
        assert stats["total_cost_usd"] == 0.0
        assert stats["budget_exceeded"] is False

    @pytest.mark.asyncio
    async def test_start_stop(self, manager):
        await manager.start()
        assert manager._running
        await manager.stop()
        assert not manager._running

    def test_record_llm_cost(self, manager):
        response = LLMResponse(
            content="Hello",
            model="xiaomi/mimo-v2.5-pro",
            tokens_input=10000,
            tokens_output=5000,
        )
        manager.record_llm_cost(response)
        
        stats = manager.get_stats()
        assert stats["total_cost_usd"] > 0

    def test_record_multiple_costs(self, manager):
        for i in range(5):
            response = LLMResponse(
                content=f"Response {i}",
                model="xiaomi/mimo-v2.5-pro",
                tokens_input=1000,
                tokens_output=500,
            )
            manager.record_llm_cost(response)
        
        stats = manager.get_stats()
        assert stats["total_cost_usd"] > 0
        assert stats["total_events"] == 5

    def test_budget_status_ok(self, manager):
        status = manager.get_budget_status()
        assert "🟢 OK" in status

    def test_budget_status_warning(self, manager):
        # Force warning state
        manager._downgraded = True
        manager._monitor._total_cost = 40.0  # 80% of 50 budget
        
        status = manager.get_budget_status()
        assert "🟡" in status or "🔴" in status

    def test_get_report(self, manager):
        response = LLMResponse(
            content="test",
            model="xiaomi/mimo-v2.5-pro",
            tokens_input=100,
            tokens_output=50,
        )
        manager.record_llm_cost(response)
        
        report = manager.get_report()
        assert "total_cost_usd" in report
        assert "budget_exceeded" in report
        assert "warning_threshold" in report

    def test_get_preferred_model(self, manager, router):
        model = manager.get_preferred_model("chat")
        assert model is not None

    def test_get_preferred_model_budget_low(self, manager):
        # Force budget exceeded
        manager._budget_exceeded = True
        
        model = manager.get_preferred_model("chat")
        assert model is not None

    def test_reset_budget_alerts(self, manager):
        manager._budget_exceeded = True
        manager._downgraded = True
        
        manager.reset_budget_alerts()
        
        assert manager._budget_exceeded is False
        assert manager._downgraded is False

    def test_no_llm_manager(self, manager_no_llm):
        response = LLMResponse(
            content="test",
            model="test",
            tokens_input=100,
            tokens_output=50,
        )
        # Should not crash
        manager_no_llm.record_llm_cost(response)
        
        stats = manager_no_llm.get_stats()
        assert stats["total_cost_usd"] == 0.0  # No config, so cost = 0

    def test_get_preferred_model_no_router(self, manager_no_llm):
        model = manager_no_llm.get_preferred_model("chat")
        assert model is None

    def test_stats_comprehensive(self, manager):
        response = LLMResponse(
            content="test",
            model="xiaomi/mimo-v2.5-pro",
            tokens_input=100,
            tokens_output=50,
        )
        manager.record_llm_cost(response)
        
        stats = manager.get_stats()
        assert "total_cost_usd" in stats
        assert "budget_exceeded" in stats
        assert "downgraded" in stats
        assert "warning_threshold" in stats
        assert "critical_threshold" in stats
        assert "budget_status" in stats
