"""
Tests for ORION Intelligence (LLM Client + Model Router)
=========================================================
"""

import asyncio
import pytest
import time
from unittest.mock import patch, AsyncMock, MagicMock

from orion.intelligence.llm_client import (
    LLMClient, LLMMessage, LLMResponse, ModelConfig, DEFAULT_MODELS
)
from orion.intelligence.model_router import ModelRouter, TaskType


@pytest.fixture
def client():
    return LLMClient(default_model="mimo-v2.5-pro")


@pytest.fixture
def router(client):
    return ModelRouter(client)


# ── LLM Client Tests ────────────────────────────────────────

class TestLLMClient:
    def test_initial_state(self, client):
        assert client._default_model == "mimo-v2.5-pro"
        assert len(client._models) >= 1

    def test_list_models(self, client):
        models = client.list_models()
        assert "mimo-v2.5-pro" in models
        assert "mimo-v2.5" in models

    def test_get_model(self, client):
        config = client.get_model("mimo-v2.5-pro")
        assert config.model_id == "xiaomi/mimo-v2.5-pro"
        assert "openrouter" in config.base_url

    def test_get_model_unknown(self, client):
        with pytest.raises(ValueError, match="Unknown model"):
            client.get_model("nonexistent")

    def test_add_model(self, client):
        custom = ModelConfig(
            model_id="custom/model",
            base_url="https://api.custom.com/v1",
            api_key="test-key",
        )
        client.add_model("custom", custom)
        assert "custom" in client.list_models()

    def test_default_models_config(self):
        for name, config in DEFAULT_MODELS.items():
            assert config.model_id
            assert config.base_url
            assert config.api_key
            assert config.max_tokens > 0

    def test_stats_initial(self, client):
        stats = client.get_stats()
        assert stats["total_calls"] == 0
        assert stats["default_model"] == "mimo-v2.5-pro"

    @pytest.mark.asyncio
    async def test_chat_mock(self, client):
        """Test chat with mocked HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "xiaomi/mimo-v2.5-pro",
            "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        client._client = mock_client
        
        response = await client.chat("Hi")
        
        assert response.content == "Hello!"
        assert response.tokens_input == 10
        assert response.tokens_output == 5
        assert response.model == "xiaomi/mimo-v2.5-pro"

    @pytest.mark.asyncio
    async def test_chat_with_system(self, client):
        """Test chat with system prompt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "xiaomi/mimo-v2.5-pro",
            "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 3},
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        client._client = mock_client
        
        response = await client.chat("Test", system="You are helpful.")
        
        # Verify system prompt was included
        call_args = mock_client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        messages = payload["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, client):
        """Test error handling on HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = Exception("500 error")
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False
        client._client = mock_client
        client._max_retries = 1
        
        with pytest.raises(RuntimeError, match="LLM call failed"):
            await client.chat("Test")

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close."""
        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        client._client = mock_client
        
        await client.close()
        mock_client.aclose.assert_called_once()

    def test_llm_message(self):
        msg = LLMMessage("user", "Hello")
        assert msg.to_dict() == {"role": "user", "content": "Hello"}

    def test_llm_message_with_name(self):
        msg = LLMMessage("user", "Hello", name="test")
        d = msg.to_dict()
        assert d["name"] == "test"

    def test_llm_response(self):
        resp = LLMResponse(
            content="Hi",
            model="test",
            tokens_input=10,
            tokens_output=5,
            latency_ms=100.0,
        )
        assert resp.content == "Hi"
        assert resp.finish_reason == "stop"


# ── Model Router Tests ──────────────────────────────────────

class TestModelRouter:
    def test_select_model_chat(self, router):
        model = router.select_model(TaskType.CHAT)
        assert model in ("mimo-v2.5-pro", "mimo-v2.5")

    def test_select_model_code(self, router):
        model = router.select_model(TaskType.CODE)
        assert model in ("mimo-v2.5-pro", "mimo-v2.5")

    def test_select_model_prefer_speed(self, router):
        model = router.select_model(TaskType.CHAT, prefer_speed=True)
        assert model is not None

    def test_select_model_with_cost_limit(self, router):
        model = router.select_model(TaskType.CHAT, max_cost_per_1k=0.0001)
        assert model is not None

    def test_select_model_exclude(self, router):
        model = router.select_model(TaskType.CHAT, exclude=["mimo-v2.5-pro"])
        assert model != "mimo-v2.5-pro"

    def test_get_fallback_chain(self, router):
        chain = router.get_fallback_chain("mimo-v2.5-pro")
        assert "mimo-v2.5-pro" in chain
        assert len(chain) >= 1

    def test_stats(self, router):
        stats = router.get_stats()
        assert "available_models" in stats
        assert stats["total_routes"] == 0

    def test_routing_history(self, router):
        router._routing_history.append({
            "task_type": "chat",
            "model": "mimo-v2.5-pro",
            "success": True,
            "timestamp": time.time(),
        })
        stats = router.get_stats()
        assert stats["total_routes"] == 1

    @pytest.mark.asyncio
    async def test_route_and_call_mock(self, router):
        """Test route_and_call with mocked client."""
        mock_response = LLMResponse(
            content="Test response",
            model="xiaomi/mimo-v2.5-pro",
            tokens_input=10,
            tokens_output=5,
        )
        
        router._client.chat = AsyncMock(return_value=mock_response)
        
        response = await router.route_and_call("Hello", task_type=TaskType.CHAT)
        
        assert response.content == "Test response"
        assert len(router._routing_history) == 1


# ── Task Type Tests ─────────────────────────────────────────

class TestTaskType:
    def test_all_types(self):
        assert TaskType.CHAT == "chat"
        assert TaskType.CODE == "code"
        assert TaskType.ANALYSIS == "analysis"
        assert TaskType.CREATIVE == "creative"
        assert TaskType.REASONING == "reasoning"
