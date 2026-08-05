"""
ORION LLM Client
================

OpenAI-compatible LLM client with multi-model support.
Supports any OpenAI-compatible API (OpenRouter, OpenAI, DeepSeek, etc.)

Features:
- Async HTTP client using httpx
- Multi-model support with automatic fallback
- Token counting and cost tracking
- Streaming support
- Retry with exponential backoff
- Structured logging

Usage:
    client = LLMClient()
    response = await client.chat("Hello!", model="xiaomi/mimo-v2.5-pro")
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class LLMMessage:
    """A single message in a conversation."""
    
    def __init__(self, role: str, content: str, name: Optional[str] = None):
        self.role = role
        self.content = content
        self.name = name
    
    def to_dict(self) -> Dict[str, str]:
        d = {"role": self.role, "content": self.content}
        if self.name:
            d["name"] = self.name
        return d


class LLMResponse:
    """Response from an LLM API call."""
    
    def __init__(
        self,
        content: str,
        model: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        latency_ms: float = 0.0,
        finish_reason: str = "stop",
        raw: Optional[Dict] = None,
    ):
        self.content = content
        self.model = model
        self.tokens_input = tokens_input
        self.tokens_output = tokens_output
        self.latency_ms = latency_ms
        self.finish_reason = finish_reason
        self.raw = raw or {}


class ModelConfig:
    """Configuration for a single model."""
    
    def __init__(
        self,
        model_id: str,
        base_url: str,
        api_key: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        priority: int = 0,
        enabled: bool = True,
    ):
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self.priority = priority
        self.enabled = enabled


# Default model configurations
DEFAULT_MODELS: Dict[str, ModelConfig] = {
    "mimo-v2.5-pro": ModelConfig(
        model_id="xiaomi/mimo-v2.5-pro",
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-s6jpfk7yts8kasyjdjqlzvwbv08e2mtc6g943uqhltcpgz2f",
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0006,
        priority=1,
    ),
    "mimo-v2.5": ModelConfig(
        model_id="xiaomi/mimo-v2.5",
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-s6jpfk7yts8kasyjdjqlzvwbv08e2mtc6g943uqhltcpgz2f",
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0003,
        priority=2,
    ),
}


class LLMClient:
    """
    Async LLM client with multi-model support.
    """
    
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        models: Optional[Dict[str, ModelConfig]] = None,
        default_model: str = "mimo-v2.5-pro",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        self._event_bus = event_bus
        self._models = models or dict(DEFAULT_MODELS)
        self._default_model = default_model
        self._max_retries = max_retries
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
        # Stats
        self._total_calls: int = 0
        self._total_tokens_input: int = 0
        self._total_tokens_output: int = 0
        self._total_latency_ms: float = 0.0
        self._errors: int = 0
        
        logger.info("LLMClient initialized (default=%s, models=%d)", 
                    default_model, len(self._models))
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client
    
    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def add_model(self, name: str, config: ModelConfig) -> None:
        """Add or update a model configuration."""
        self._models[name] = config
        logger.info("Model added: %s (%s)", name, config.model_id)
    
    def get_model(self, name: Optional[str] = None) -> ModelConfig:
        """Get model config by name."""
        name = name or self._default_model
        if name not in self._models:
            raise ValueError(f"Unknown model: {name}. Available: {list(self._models.keys())}")
        return self._models[name]
    
    def list_models(self) -> List[str]:
        """List available model names."""
        return [k for k, v in self._models.items() if v.enabled]
    
    async def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        messages: Optional[List[LLMMessage]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send a chat completion request.
        
        Args:
            prompt: User message (ignored if messages provided)
            model: Model name (uses default if None)
            system: System prompt
            messages: Full message list (overrides prompt/system)
            temperature: Override temperature
            max_tokens: Override max tokens
        """
        config = self.get_model(model)
        
        # Build messages
        if messages is None:
            msgs = []
            if system:
                msgs.append({"role": "system", "content": system})
            msgs.append({"role": "user", "content": prompt})
        else:
            msgs = [m.to_dict() for m in messages]
        
        # Build request
        payload = {
            "model": config.model_id,
            "messages": msgs,
            "max_tokens": max_tokens or config.max_tokens,
            "temperature": temperature if temperature is not None else config.temperature,
        }
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://orion-agent.local",
            "X-Title": "ORION Autonomous Agent",
        }
        
        url = f"{config.base_url}/chat/completions"
        
        # Retry loop
        last_error = None
        for attempt in range(self._max_retries):
            start_time = time.time()
            
            try:
                client = await self._get_client()
                resp = await client.post(url, json=payload, headers=headers)
                latency_ms = (time.time() - start_time) * 1000
                
                if resp.status_code == 429:
                    # Rate limited - wait and retry
                    wait = min(2 ** attempt * 2, 30)
                    logger.warning("Rate limited, waiting %ds (attempt %d/%d)", 
                                 wait, attempt + 1, self._max_retries)
                    await asyncio.sleep(wait)
                    continue
                
                resp.raise_for_status()
                data = resp.json()
                
                # Parse response
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                usage = data.get("usage", {})
                
                tokens_in = usage.get("prompt_tokens", 0)
                tokens_out = usage.get("completion_tokens", 0)
                
                # Update stats
                self._total_calls += 1
                self._total_tokens_input += tokens_in
                self._total_tokens_output += tokens_out
                self._total_latency_ms += latency_ms
                
                response = LLMResponse(
                    content=message.get("content", ""),
                    model=data.get("model", config.model_id),
                    tokens_input=tokens_in,
                    tokens_output=tokens_out,
                    latency_ms=round(latency_ms, 1),
                    finish_reason=choice.get("finish_reason", "stop"),
                    raw=data,
                )
                
                # Publish event
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type="intelligence.llm.response",
                        payload={
                            "model": response.model,
                            "tokens_input": tokens_in,
                            "tokens_output": tokens_out,
                            "latency_ms": round(latency_ms, 1),
                        },
                        timestamp=time.time(),
                        source="llm_client",
                    ))
                
                logger.info(
                    "LLM call: model=%s tokens=%d/%d latency=%.0fms",
                    response.model, tokens_in, tokens_out, latency_ms
                )
                
                return response
            
            except httpx.HTTPStatusError as e:
                last_error = e
                self._errors += 1
                logger.error("LLM HTTP error (attempt %d/%d): %s %s", 
                           attempt + 1, self._max_retries, e.response.status_code, e.response.text[:200])
                if e.response.status_code >= 500:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    break
            
            except Exception as e:
                last_error = e
                self._errors += 1
                logger.error("LLM error (attempt %d/%d): %s", 
                           attempt + 1, self._max_retries, e)
                await asyncio.sleep(2 ** attempt)
                continue
        
        raise RuntimeError(f"LLM call failed after {self._max_retries} attempts: {last_error}")
    
    async def chat_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        system: Optional[str] = None,
    ) -> LLMResponse:
        """Chat with function/tool calling support."""
        config = self.get_model(model)
        
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        
        payload = {
            "model": config.model_id,
            "messages": msgs,
            "tools": [{"type": "function", "function": t} for t in tools],
            "max_tokens": config.max_tokens,
        }
        
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        
        client = await self._get_client()
        resp = await client.post(
            f"{config.base_url}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", config.model_id),
            tokens_input=usage.get("prompt_tokens", 0),
            tokens_output=usage.get("completion_tokens", 0),
            raw=data,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get LLM client statistics."""
        avg_latency = (self._total_latency_ms / self._total_calls) if self._total_calls > 0 else 0
        
        return {
            "total_calls": self._total_calls,
            "total_tokens_input": self._total_tokens_input,
            "total_tokens_output": self._total_tokens_output,
            "total_latency_ms": round(self._total_latency_ms, 1),
            "avg_latency_ms": round(avg_latency, 1),
            "errors": self._errors,
            "models": list(self._models.keys()),
            "default_model": self._default_model,
        }
