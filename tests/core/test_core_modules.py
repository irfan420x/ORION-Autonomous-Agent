"""
Tests for ORION Core Modules (Error Classifier, Tool Dispatcher, Message Manager)
=================================================================================
"""

import asyncio
import pytest

from orion.core.error_classifier import (
    classify_error, should_retry, format_error,
    ErrorCategory, RetryStrategy
)
from orion.core.tool_dispatcher import ToolDispatcher, ToolResult
from orion.core.message_manager import MessageManager


# ── Error Classifier Tests ───────────────────────────────────

class TestErrorClassifier:
    def test_transient_error(self):
        err = Exception("Connection timed out")
        cat, strategy = classify_error(err)
        assert cat == ErrorCategory.TRANSIENT
        assert strategy.max_retries > 0

    def test_rate_limit_error(self):
        err = Exception("429 Too Many Requests")
        cat, strategy = classify_error(err)
        assert cat == ErrorCategory.RATE_LIMIT

    def test_auth_error(self):
        err = Exception("401 Unauthorized")
        cat, strategy = classify_error(err)
        assert cat == ErrorCategory.AUTH

    def test_permanent_error(self):
        err = Exception("400 Bad Request")
        cat, strategy = classify_error(err)
        assert cat == ErrorCategory.PERMANENT

    def test_unknown_error(self):
        err = Exception("Something weird happened")
        cat, strategy = classify_error(err)
        assert cat == ErrorCategory.UNKNOWN

    def test_should_retry_transient(self):
        err = Exception("timeout")
        retry, delay = should_retry(err, 0)
        assert retry is True
        assert delay > 0

    def test_should_not_retry_permanent(self):
        err = Exception("400 Bad Request")
        retry, delay = should_retry(err, 0)
        assert retry is False

    def test_format_error(self):
        err = Exception("timeout")
        msg = format_error(err)
        assert "Network" in msg or "Retrying" in msg

    def test_retry_strategy_delay(self):
        strategy = RetryStrategy(base_delay=1.0, backoff_factor=2.0, jitter=False)
        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 2.0
        assert strategy.get_delay(2) == 4.0


# ── Tool Dispatcher Tests ────────────────────────────────────

class TestToolDispatcher:
    def test_register(self):
        dispatcher = ToolDispatcher()
        dispatcher.register("test", lambda: "ok")
        assert "test" in dispatcher._tools

    @pytest.mark.asyncio
    async def test_execute_success(self):
        dispatcher = ToolDispatcher()
        dispatcher.register("test", lambda: "ok")
        result = await dispatcher.execute("test", {})
        assert result.success is True
        assert result.output == "ok"

    @pytest.mark.asyncio
    async def test_execute_async(self):
        dispatcher = ToolDispatcher()
        async def async_tool():
            return "async ok"
        dispatcher.register("test", async_tool)
        result = await dispatcher.execute("test", {})
        assert result.success is True
        assert result.output == "async ok"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        dispatcher = ToolDispatcher()
        result = await dispatcher.execute("nonexistent", {})
        assert result.success is False
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_error(self):
        dispatcher = ToolDispatcher()
        def failing_tool():
            raise ValueError("test error")
        dispatcher.register("fail", failing_tool)
        result = await dispatcher.execute("fail", {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_batch(self):
        dispatcher = ToolDispatcher()
        dispatcher.register("a", lambda: "A")
        dispatcher.register("b", lambda: "B")
        results = await dispatcher.execute_batch([("a", {}), ("b", {})])
        assert len(results) == 2
        assert results[0].output == "A"
        assert results[1].output == "B"

    @pytest.mark.asyncio
    async def test_budget_tracking(self):
        dispatcher = ToolDispatcher()
        dispatcher.register("test", lambda: "x" * 100)
        await dispatcher.execute("test", {})
        stats = dispatcher.get_stats()
        assert stats["turn_budget_used"] > 0

    def test_tool_result_message(self):
        result = ToolResult("test", True, "output")
        msg = result.to_message()
        assert "test" in msg
        assert "output" in msg


# ── Message Manager Tests ────────────────────────────────────

class TestMessageManager:
    def test_add_user(self):
        mgr = MessageManager()
        mgr.add_user("hello")
        msgs = mgr.get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_add_assistant(self):
        mgr = MessageManager()
        mgr.add_user("hello")
        mgr.add_assistant("hi there")
        msgs = mgr.get_messages()
        assert len(msgs) == 2

    def test_add_system(self):
        mgr = MessageManager()
        mgr.add_system("You are ORION")
        mgr.add_user("hello")
        msgs = mgr.get_messages()
        assert msgs[0]["role"] == "system"

    def test_trim_by_count(self):
        mgr = MessageManager(max_messages=3)
        for i in range(10):
            mgr.add_user(f"msg {i}")
        msgs = mgr.get_messages()
        assert len(msgs) == 3

    def test_trim_preserves_system(self):
        mgr = MessageManager(max_messages=3)
        mgr.add_system("system")
        for i in range(10):
            mgr.add_user(f"msg {i}")
        msgs = mgr.get_messages()
        assert msgs[0]["role"] == "system"

    def test_get_history_text(self):
        mgr = MessageManager()
        mgr.add_user("hello")
        mgr.add_assistant("hi")
        text = mgr.get_history_text()
        assert "USER" in text
        assert "ASSISTANT" in text

    def test_clear(self):
        mgr = MessageManager()
        mgr.add_user("hello")
        mgr.clear()
        assert len(mgr.get_messages()) == 0

    def test_stats(self):
        mgr = MessageManager()
        mgr.add_user("hello")
        stats = mgr.get_stats()
        assert stats["message_count"] == 1
