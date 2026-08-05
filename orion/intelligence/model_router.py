"""
ORION Model Router
==================

Selects the best LLM model based on task requirements.
Routes based on: cost, latency, quality, capabilities.

Features:
- Task-based routing (code, chat, analysis, creative)
- Cost-aware selection
- Fallback chains
- Performance tracking

Usage:
    router = ModelRouter(llm_client)
    model = router.select_model(task_type="code", max_cost=0.01)
"""

import logging
import time
from typing import Any, Dict, List, Optional

from orion.intelligence.llm_client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)


class TaskType:
    """Task types for routing."""
    CHAT = "chat"
    CODE = "code"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


# Model capabilities (what each model is good at)
MODEL_CAPABILITIES: Dict[str, Dict[str, float]] = {
    "mimo-v2.5-pro": {
        "chat": 0.9,
        "code": 0.85,
        "analysis": 0.85,
        "creative": 0.8,
        "reasoning": 0.9,
        "summarization": 0.85,
        "translation": 0.8,
    },
    "mimo-v2.5": {
        "chat": 0.8,
        "code": 0.75,
        "analysis": 0.75,
        "creative": 0.7,
        "reasoning": 0.8,
        "summarization": 0.75,
        "translation": 0.7,
    },
}


class ModelRouter:
    """
    Routes tasks to the best available model.
    """
    
    def __init__(self, llm_client: LLMClient):
        self._client = llm_client
        self._routing_history: List[Dict[str, Any]] = []
        self._max_history: int = 100
        
        logger.info("ModelRouter initialized")
    
    def select_model(
        self,
        task_type: str = TaskType.CHAT,
        max_cost_per_1k: Optional[float] = None,
        prefer_speed: bool = False,
        exclude: Optional[List[str]] = None,
    ) -> str:
        """
        Select the best model for a task.
        
        Args:
            task_type: Type of task (chat, code, analysis, etc.)
            max_cost_per_1k: Max cost per 1k tokens
            prefer_speed: Prefer faster (cheaper) models
            exclude: Models to exclude
        """
        exclude = set(exclude or [])
        candidates = []
        
        for name, config in self._client._models.items():
            if not config.enabled or name in exclude:
                continue
            if max_cost_per_1k and config.cost_per_1k_input > max_cost_per_1k:
                continue
            
            caps = MODEL_CAPABILITIES.get(name, {})
            quality = caps.get(task_type, 0.5)
            
            # Score: quality weighted by cost efficiency
            cost_factor = 1.0 / (config.cost_per_1k_input + 0.0001)
            
            if prefer_speed:
                score = quality * 0.3 + cost_factor * 0.7
            else:
                score = quality * 0.7 + cost_factor * 0.3
            
            candidates.append((name, score, quality))
        
        if not candidates:
            # Fallback to default
            default = self._client._default_model
            logger.warning("No candidates found, using default: %s", default)
            return default
        
        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        selected = candidates[0][0]
        
        logger.info(
            "Model selected: %s (task=%s, quality=%.2f, candidates=%d)",
            selected, task_type, candidates[0][2], len(candidates)
        )
        
        return selected
    
    def get_fallback_chain(self, primary: str, task_type: str = TaskType.CHAT) -> List[str]:
        """Get a fallback chain of models for a task."""
        chain = [primary]
        
        for name, config in sorted(
            self._client._models.items(),
            key=lambda x: x[1].priority
        ):
            if name != primary and config.enabled:
                chain.append(name)
        
        return chain
    
    async def route_and_call(
        self,
        prompt: str,
        task_type: str = TaskType.CHAT,
        system: Optional[str] = None,
        max_cost_per_1k: Optional[float] = None,
    ) -> LLMResponse:
        """
        Select model and make a call with fallback.
        """
        model_name = self.select_model(task_type, max_cost_per_1k)
        chain = self.get_fallback_chain(model_name, task_type)
        
        last_error = None
        for name in chain:
            try:
                response = await self._client.chat(
                    prompt=prompt,
                    model=name,
                    system=system,
                )
                
                # Track routing
                self._routing_history.append({
                    "task_type": task_type,
                    "model": name,
                    "success": True,
                    "timestamp": time.time(),
                })
                if len(self._routing_history) > self._max_history:
                    self._routing_history.pop(0)
                
                return response
            
            except Exception as e:
                last_error = e
                logger.warning("Model %s failed, trying fallback: %s", name, e)
                
                self._routing_history.append({
                    "task_type": task_type,
                    "model": name,
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time(),
                })
                continue
        
        raise RuntimeError(f"All models failed for task '{task_type}': {last_error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total = len(self._routing_history)
        successful = sum(1 for r in self._routing_history if r.get("success"))
        
        # Model usage counts
        model_counts: Dict[str, int] = {}
        for r in self._routing_history:
            m = r.get("model", "unknown")
            model_counts[m] = model_counts.get(m, 0) + 1
        
        return {
            "total_routes": total,
            "successful": successful,
            "failed": total - successful,
            "model_usage": model_counts,
            "available_models": self._client.list_models(),
        }
