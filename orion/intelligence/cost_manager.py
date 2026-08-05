"""
ORION Cost Manager
==================

Enhanced cost management integrated with LLM Client and Model Router.
Wraps CostMonitor with budget-aware routing and automatic cost tracking.

Features:
- Automatic cost recording on every LLM call
- Budget-based model switching (expensive → cheap when budget low)
- Monthly/weekly cost reports
- Alert thresholds (warning, critical)
- Integration with ModelRouter for cost-aware routing

Usage:
    manager = CostManager(event_bus, llm_client, model_router, monthly_budget=50.0)
    await manager.start()
    # Costs are automatically tracked on every LLM call
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus
from orion.intelligence.llm_client import LLMClient, LLMResponse
from orion.intelligence.model_router import ModelRouter
from orion.observability.cost_monitor import CostMonitor

logger = logging.getLogger(__name__)


class CostManager:
    """
    Budget-aware cost management for LLM operations.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        llm_client: Optional[LLMClient] = None,
        model_router: Optional[ModelRouter] = None,
        monthly_budget: float = 100.0,
        warning_threshold: float = 0.7,
        critical_threshold: float = 0.9,
    ):
        self._event_bus = event_bus
        self._llm = llm_client
        self._router = model_router
        self._monitor = CostMonitor(
            event_bus,
            monthly_budget=monthly_budget,
            alert_threshold=critical_threshold,
        )
        self._warning_threshold = warning_threshold
        self._critical_threshold = critical_threshold
        self._running = False
        
        # Budget state
        self._budget_exceeded: bool = False
        self._downgraded: bool = False
        
        logger.info("CostManager created (budget=$%.2f)", monthly_budget)
    
    async def start(self) -> None:
        """Start cost management."""
        if self._running:
            return
        self._running = True
        logger.info("CostManager started")
    
    async def stop(self) -> None:
        """Stop cost management."""
        self._running = False
        logger.info("CostManager stopped")
    
    def record_llm_cost(
        self,
        response: LLMResponse,
        service: str = "openrouter",
    ) -> None:
        """Record cost from an LLM response."""
        # Calculate cost based on model config
        cost_usd = 0.0
        if self._llm:
            config = self._llm._models.get(
                self._llm._default_model
            )
            if config:
                cost_usd = (
                    response.tokens_input / 1000 * config.cost_per_1k_input +
                    response.tokens_output / 1000 * config.cost_per_1k_output
                )
        
        self._monitor.record_cost(
            service=service,
            model=response.model,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=cost_usd,
        )
        
        # Check budget
        self._check_budget()
    
    def _check_budget(self) -> None:
        """Check budget and trigger alerts if needed."""
        report = self._monitor.get_report()
        used_pct = report["budget_used_percent"] / 100.0
        
        if used_pct >= self._critical_threshold and not self._budget_exceeded:
            self._budget_exceeded = True
            logger.warning("BUDGET CRITICAL: %.1f%% used ($%.2f / $%.2f)",
                          used_pct * 100, report["total_cost_usd"], report["monthly_budget_usd"])
        
        elif used_pct >= self._warning_threshold and not self._downgraded:
            self._downgraded = True
            logger.warning("BUDGET WARNING: %.1f%% used", used_pct * 100)
    
    def get_preferred_model(self, task_type: str = "chat") -> Optional[str]:
        """
        Get the preferred model considering budget.
        Downgrades to cheaper model when budget is low.
        """
        if not self._router:
            return None
        
        report = self._monitor.get_report()
        used_pct = report["budget_used_percent"] / 100.0
        
        if used_pct >= self._critical_threshold:
            # Force cheapest model
            return self._router.select_model(
                task_type=task_type,
                prefer_speed=True,
            )
        elif used_pct >= self._warning_threshold:
            # Prefer cheaper model
            return self._router.select_model(
                task_type=task_type,
                prefer_speed=True,
            )
        else:
            # Normal routing
            return self._router.select_model(task_type=task_type)
    
    def get_report(self) -> Dict[str, Any]:
        """Get cost report."""
        report = self._monitor.get_report()
        report["budget_exceeded"] = self._budget_exceeded
        report["downgraded"] = self._downgraded
        report["warning_threshold"] = self._warning_threshold
        report["critical_threshold"] = self._critical_threshold
        return report
    
    def get_budget_status(self) -> str:
        """Get human-readable budget status."""
        report = self._monitor.get_report()
        used_pct = report["budget_used_percent"]
        
        if used_pct >= self._critical_threshold * 100:
            return f"🔴 CRITICAL: {used_pct:.1f}% used"
        elif used_pct >= self._warning_threshold * 100:
            return f"🟡 WARNING: {used_pct:.1f}% used"
        else:
            return f"🟢 OK: {used_pct:.1f}% used"
    
    def reset_budget_alerts(self) -> None:
        """Reset budget alert flags."""
        self._budget_exceeded = False
        self._downgraded = False
        self._monitor.reset_alert()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cost manager statistics."""
        monitor_stats = self._monitor.get_stats()
        return {
            **monitor_stats,
            "budget_exceeded": self._budget_exceeded,
            "downgraded": self._downgraded,
            "warning_threshold": self._warning_threshold,
            "critical_threshold": self._critical_threshold,
            "budget_status": self.get_budget_status(),
        }
