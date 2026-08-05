"""
ORION Metrics Collector
========================

Collects, stores, and queries system metrics.
Supports counters, gauges, and histograms.

Features:
- In-memory metric storage with configurable retention
- Label-based filtering
- Aggregation (avg, min, max, sum, count)
- Event publishing via EventBus
- Auto-collection of system metrics

Usage:
    collector = MetricsCollector(event_bus)
    await collector.start()
    collector.record("cpu_percent", 45.2, MetricType.GAUGE)
    metrics = collector.query("cpu_percent")
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

import psutil

from orion.contracts.agent_contracts import Event
from orion.contracts.observability_contracts import MetricType, MetricValue
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and stores system and application metrics.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        max_metrics_per_name: int = 1000,
        collection_interval: float = 10.0,
    ):
        self._event_bus = event_bus
        self._max_per_name = max_metrics_per_name
        self._collection_interval = collection_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # Storage: metric_name -> list of MetricValue
        self._metrics: Dict[str, List[MetricValue]] = defaultdict(list)
        
        # Stats
        self._total_collected: int = 0
        self._total_queries: int = 0
        
        logger.info("MetricsCollector created")
    
    async def start(self) -> None:
        """Start auto-collection of system metrics."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("MetricsCollector started")
    
    async def stop(self) -> None:
        """Stop metric collection."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MetricsCollector stopped")
    
    def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "",
        timestamp: Optional[float] = None,
    ) -> None:
        """Record a metric value."""
        metric = MetricValue(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            timestamp=timestamp or time.time(),
            unit=unit,
        )
        
        self._metrics[name].append(metric)
        self._total_collected += 1
        
        # Trim if too many
        if len(self._metrics[name]) > self._max_per_name:
            self._metrics[name] = self._metrics[name][-self._max_per_name:]
    
    def _get_last_value(self, name: str) -> Optional[float]:
        """Get the last recorded value for a metric."""
        metrics = self._metrics.get(name, [])
        return metrics[-1].value if metrics else None
    
    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        # Get current total
        current = self._get_last_value(name) or 0
        self.record(name, current + value, MetricType.COUNTER, labels)
    
    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, unit: str = "") -> None:
        """Set a gauge metric."""
        self.record(name, value, MetricType.GAUGE, labels, unit)
    
    def query(
        self,
        name: str,
        limit: int = 100,
        since: Optional[float] = None,
    ) -> List[MetricValue]:
        """Query metric values by name."""
        self._total_queries += 1
        
        metrics = self._metrics.get(name, [])
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return metrics[-limit:]
    
    def query_latest(self, name: str) -> Optional[MetricValue]:
        """Get the latest value for a metric."""
        metrics = self._metrics.get(name, [])
        return metrics[-1] if metrics else None
    
    def aggregate(
        self,
        name: str,
        func: str = "avg",
        since: Optional[float] = None,
    ) -> Optional[float]:
        """Aggregate metric values (avg, min, max, sum, count)."""
        metrics = self.query(name, limit=10000, since=since)
        
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        if func == "avg":
            return sum(values) / len(values)
        elif func == "min":
            return min(values)
        elif func == "max":
            return max(values)
        elif func == "sum":
            return sum(values)
        elif func == "count":
            return float(len(values))
        elif func == "latest":
            return values[-1]
        else:
            return None
    
    def get_all_metric_names(self) -> List[str]:
        """Get all metric names."""
        return list(self._metrics.keys())
    
    def get_metric_count(self) -> int:
        """Get total number of distinct metrics."""
        return len(self._metrics)
    
    # ── Auto Collection ───────────────────────────────────────
    
    async def _collection_loop(self) -> None:
        """Periodically collect system metrics."""
        while self._running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self._collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Metric collection error: %s", e)
                await asyncio.sleep(self._collection_interval)
    
    async def _collect_system_metrics(self) -> None:
        """Collect CPU, RAM, Disk metrics."""
        now = time.time()
        
        # CPU
        cpu = psutil.cpu_percent(interval=0)
        self.gauge("system.cpu.percent", cpu, unit="percent")
        
        # RAM
        ram = psutil.virtual_memory()
        self.gauge("system.ram.percent", ram.percent, unit="percent")
        self.gauge("system.ram.available_gb", round(ram.available / (1024**3), 2), unit="GB")
        
        # Disk
        disk = psutil.disk_usage("/")
        self.gauge("system.disk.percent", disk.percent, unit="percent")
        self.gauge("system.disk.free_gb", round(disk.free / (1024**3), 2), unit="GB")
        
        # Publish metrics event
        await self._event_bus.publish(Event(
            event_type="system.metrics.collected",
            payload={
                "cpu_percent": cpu,
                "ram_percent": ram.percent,
                "disk_percent": disk.percent,
                "timestamp": now,
            },
            timestamp=now,
            source="metrics_collector",
        ))
    
    # ── Statistics ────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        total_values = sum(len(v) for v in self._metrics.values())
        return {
            "running": self._running,
            "total_collected": self._total_collected,
            "total_queries": self._total_queries,
            "distinct_metrics": len(self._metrics),
            "total_values_stored": total_values,
            "collection_interval": self._collection_interval,
        }
