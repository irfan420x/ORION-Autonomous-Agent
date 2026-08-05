"""
ORION Cost Monitor
==================

Tracks costs from LLM API calls and other services.
Provides budgeting, alerts, and cost reports.

Features:
- Track cost events per service/model
- Budget limits with alerts
- Cost breakdown by service, model, operation
- Event publishing via EventBus

Usage:
    monitor = CostMonitor(event_bus, monthly_budget=50.0)
    monitor.record_cost("openai", "gpt-4", 1000, 500, 0.03)
    report = monitor.get_report()
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.contracts.observability_contracts import CostEvent
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class CostMonitor:
    """
    Tracks and monitors costs from LLM API calls.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        monthly_budget: float = 100.0,
        alert_threshold: float = 0.8,
    ):
        self._event_bus = event_bus
        self._monthly_budget = monthly_budget
        self._alert_threshold = alert_threshold  # Alert at 80% by default
        
        # Cost events
        self._events: List[CostEvent] = []
        self._max_events: int = 10000
        
        # Stats
        self._total_cost: float = 0.0
        self._total_tokens_input: int = 0
        self._total_tokens_output: int = 0
        self._alert_sent: bool = False
        
        logger.info("CostMonitor created (budget=$%.2f)", monthly_budget)
    
    def record_cost(
        self,
        service: str,
        model: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost_usd: float = 0.0,
        operation: str = "completion",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEvent:
        """Record a cost event."""
        event = CostEvent(
            event_id=uuid.uuid4().hex[:12],
            service=service,
            operation=operation,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            model=model,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        
        self._events.append(event)
        self._total_cost += cost_usd
        self._total_tokens_input += tokens_input
        self._total_tokens_output += tokens_output
        
        # Trim
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
        
        # Check budget
        if self._total_cost >= self._monthly_budget * self._alert_threshold and not self._alert_sent:
            self._alert_sent = True
            logger.warning("Cost alert: $%.2f / $%.2f (%.0f%%)",
                          self._total_cost, self._monthly_budget,
                          (self._total_cost / self._monthly_budget) * 100)
        
        return event
    
    def get_report(self) -> Dict[str, Any]:
        """Get a cost report."""
        # Breakdown by service
        by_service: Dict[str, float] = {}
        by_model: Dict[str, float] = {}
        
        for e in self._events:
            by_service[e.service] = by_service.get(e.service, 0) + e.cost_usd
            if e.model:
                by_model[e.model] = by_model.get(e.model, 0) + e.cost_usd
        
        budget_percent = (self._total_cost / self._monthly_budget * 100) if self._monthly_budget > 0 else 0
        
        return {
            "total_cost_usd": round(self._total_cost, 4),
            "monthly_budget_usd": self._monthly_budget,
            "budget_used_percent": round(budget_percent, 1),
            "remaining_budget_usd": round(max(0, self._monthly_budget - self._total_cost), 4),
            "total_events": len(self._events),
            "total_tokens_input": self._total_tokens_input,
            "total_tokens_output": self._total_tokens_output,
            "by_service": {k: round(v, 4) for k, v in by_service.items()},
            "by_model": {k: round(v, 4) for k, v in by_model.items()},
            "alert_threshold": self._alert_threshold,
            "alert_sent": self._alert_sent,
        }
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent cost events."""
        return [e.model_dump() for e in self._events[-limit:]]
    
    def reset_alert(self) -> None:
        """Reset the budget alert flag."""
        self._alert_sent = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cost monitor statistics."""
        return {
            "total_cost_usd": round(self._total_cost, 4),
            "total_events": len(self._events),
            "total_tokens_input": self._total_tokens_input,
            "total_tokens_output": self._total_tokens_output,
            "monthly_budget": self._monthly_budget,
            "budget_used_percent": round((self._total_cost / self._monthly_budget * 100) if self._monthly_budget > 0 else 0, 1),
        }
