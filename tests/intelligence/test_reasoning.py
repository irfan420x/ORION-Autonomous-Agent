"""
Tests for ORION Reasoning Engine (M3.3)
========================================
"""

import asyncio
import json
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from orion.core.communication.event_bus import EventBus
from orion.intelligence.llm_client import LLMClient, LLMResponse
from orion.intelligence.reasoning_engine import ReasoningEngine, ReasoningResult


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def llm_client():
    client = MagicMock(spec=LLMClient)
    client.chat = AsyncMock()
    return client


@pytest.fixture
def reasoner(event_bus, llm_client):
    return ReasoningEngine(event_bus, llm_client)


@pytest.fixture
def reasoner_no_llm(event_bus):
    return ReasoningEngine(event_bus)


# ── ReasoningResult Tests ────────────────────────────────────

class TestReasoningResult:
    def test_creation(self):
        result = ReasoningResult(
            is_valid=True,
            confidence=0.9,
            issues=[],
            suggestions=[],
            reasoning="All good",
        )
        assert result.is_valid is True
        assert result.confidence == 0.9

    def test_to_dict(self):
        result = ReasoningResult(
            is_valid=False,
            confidence=0.3,
            issues=["error found"],
            suggestions=["fix it"],
            reasoning="analysis",
            needs_correction=True,
        )
        d = result.to_dict()
        assert d["is_valid"] is False
        assert d["needs_correction"] is True
        assert len(d["issues"]) == 1


# ── Reasoning Engine Tests ───────────────────────────────────

class TestReasoningEngine:
    def test_initial_state(self, reasoner):
        stats = reasoner.get_stats()
        assert stats["total_analyses"] == 0
        assert stats["llm_available"] is True

    def test_initial_state_no_llm(self, reasoner_no_llm):
        stats = reasoner_no_llm.get_stats()
        assert stats["llm_available"] is False

    @pytest.mark.asyncio
    async def test_analyze_with_llm(self, reasoner, llm_client):
        """LLM analysis works."""
        llm_response = LLMResponse(
            content=json.dumps({
                "is_valid": True,
                "confidence": 0.95,
                "issues": [],
                "suggestions": [],
                "reasoning": "Result looks correct",
                "needs_correction": False,
            }),
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        result = await reasoner.analyze_result("Test task", "Success!")
        
        assert result.is_valid is True
        assert result.confidence == 0.95
        assert result.needs_correction is False

    @pytest.mark.asyncio
    async def test_analyze_with_issues(self, reasoner, llm_client):
        """LLM detects issues."""
        llm_response = LLMResponse(
            content=json.dumps({
                "is_valid": False,
                "confidence": 0.2,
                "issues": ["Missing output", "Wrong format"],
                "suggestions": ["Add proper output"],
                "reasoning": "Result is incomplete",
                "needs_correction": True,
            }),
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        result = await reasoner.analyze_result("Test", "incomplete")
        
        assert result.is_valid is False
        assert result.needs_correction is True
        assert len(result.issues) == 2

    @pytest.mark.asyncio
    async def test_analyze_heuristic_error_detection(self, reasoner_no_llm):
        """Heuristic detects error patterns."""
        result = await reasoner_no_llm.analyze_result(
            "Test", "Error: connection failed"
        )
        
        assert result.is_valid is False
        assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_analyze_heuristic_short_result(self, reasoner_no_llm):
        """Heuristic detects suspiciously short results."""
        result = await reasoner_no_llm.analyze_result("Test", "ok")
        
        assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_analyze_heuristic_valid(self, reasoner_no_llm):
        """Heuristic accepts valid results."""
        result = await reasoner_no_llm.analyze_result(
            "Test", "The task completed successfully with all requirements met."
        )
        
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_analyze_expected_outcome(self, reasoner_no_llm):
        """Heuristic checks expected outcome."""
        result = await reasoner_no_llm.analyze_result(
            "Test", "Something else", expected_outcome="specific result"
        )
        
        assert result.needs_correction is True

    @pytest.mark.asyncio
    async def test_analyze_llm_failure_fallback(self, reasoner, llm_client):
        """LLM failure falls back to heuristic."""
        llm_client.chat.side_effect = RuntimeError("LLM unavailable")
        
        result = await reasoner.analyze_result("Test", "Success!")
        
        assert result is not None
        assert "Heuristic" in result.reasoning

    @pytest.mark.asyncio
    async def test_suggest_fix(self, reasoner, llm_client):
        """Can suggest fixes."""
        llm_response = LLMResponse(
            content="Try adding error handling around the API call.",
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        analysis = ReasoningResult(
            is_valid=False,
            confidence=0.3,
            issues=["API timeout"],
            suggestions=["Add retry"],
            reasoning="analysis",
            needs_correction=True,
        )
        
        fix = await reasoner.suggest_fix(analysis)
        assert "error handling" in fix

    @pytest.mark.asyncio
    async def test_suggest_fix_no_llm(self, reasoner_no_llm):
        """Fix suggestion without LLM returns generic advice."""
        analysis = ReasoningResult(
            is_valid=False,
            confidence=0.3,
            issues=["issue1"],
            suggestions=["suggestion1"],
            reasoning="analysis",
        )
        
        fix = await reasoner_no_llm.suggest_fix(analysis)
        assert "issue1" in fix

    @pytest.mark.asyncio
    async def test_reflect(self, reasoner, llm_client):
        """Reflection works."""
        llm_response = LLMResponse(
            content=json.dumps({
                "is_valid": True,
                "confidence": 0.8,
                "issues": [],
                "suggestions": ["Use caching next time"],
                "reasoning": "Action was effective",
            }),
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        result = await reasoner.reflect("deployed app", "success")
        
        assert result.is_valid is True
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_reflect_no_llm(self, reasoner_no_llm):
        """Reflection without LLM returns basic result."""
        result = await reasoner_no_llm.reflect("action", "outcome")
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_publishes_events(self, event_bus, reasoner, llm_client):
        """Analysis publishes events."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("intelligence.reasoning.analysis", handler)
        
        llm_response = LLMResponse(
            content=json.dumps({
                "is_valid": True,
                "confidence": 0.9,
                "issues": [],
                "suggestions": [],
                "reasoning": "OK",
                "needs_correction": False,
            }),
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        await reasoner.analyze_result("Test", "Success")
        
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_stats_tracking(self, reasoner, llm_client):
        """Stats are tracked correctly."""
        llm_response = LLMResponse(
            content=json.dumps({
                "is_valid": False,
                "confidence": 0.3,
                "issues": ["issue1", "issue2"],
                "suggestions": [],
                "reasoning": "analysis",
                "needs_correction": True,
            }),
            model="test",
        )
        llm_client.chat.return_value = llm_response
        
        await reasoner.analyze_result("Test", "Bad result")
        
        stats = reasoner.get_stats()
        assert stats["total_analyses"] == 1
        assert stats["total_issues_found"] == 2
        assert stats["total_corrections"] == 1
