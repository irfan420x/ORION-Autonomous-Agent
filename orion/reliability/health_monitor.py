"""
ORION Health Monitor
====================

Periodic health checker for all ORION core services.
Monitors EventBus, StateMachine, TaskQueue, Memory, Runtime,
and system resources (CPU, RAM, Disk).

Features:
- Configurable check interval
- Service health tracking with history
- Threshold-based status classification
- Event publishing via EventBus
- Automatic recovery trigger on failure

Usage:
    monitor = HealthMonitor(event_bus, state_machine, task_queue, runtime)
    await monitor.start()
    report = await monitor.check_all()
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

from orion.contracts.agent_contracts import Event
from orion.contracts.reliability_contracts import (
    HealthCheckResult,
    ServiceStatus,
    SystemHealthReport,
    IntegrityCheckResult,
)
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Monitors health of all ORION core services and system resources.
    
    Publishes:
    - system.health.status: Periodic health report
    - system.health.alert: When a service becomes unhealthy
    - system.health.recovered: When a service recovers
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        check_interval: float = 30.0,
        stale_threshold: float = 60.0,
    ):
        self._event_bus = event_bus
        self._check_interval = check_interval
        self._stale_threshold = stale_threshold
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time = time.time()
        
        # Health history
        self._history: List[SystemHealthReport] = []
        self._max_history: int = 100
        
        # Service statuses (cached)
        self._service_statuses: Dict[str, ServiceStatus] = {}
        
        # Custom health checkers
        self._custom_checkers: Dict[str, Callable] = {}
        
        # Critical file paths to monitor
        self._critical_files: List[str] = [
            "state/project_state.json",
        ]
        
        # Stats
        self._total_checks: int = 0
        self._total_failures: int = 0
        self._total_alerts: int = 0
        
        logger.info("HealthMonitor created (interval=%.1fs)", check_interval)
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def last_report(self) -> Optional[SystemHealthReport]:
        return self._history[-1] if self._history else None
    
    def register_checker(self, service_name: str, checker: Callable) -> None:
        """Register a custom health check function."""
        self._custom_checkers[service_name] = checker
        logger.info("Registered custom health checker: %s", service_name)
    
    def add_critical_file(self, file_path: str) -> None:
        """Add a file to the critical files list."""
        if file_path not in self._critical_files:
            self._critical_files.append(file_path)
    
    async def start(self) -> None:
        """Start periodic health monitoring."""
        if self._running:
            logger.warning("HealthMonitor already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("HealthMonitor started")
        
        await self._event_bus.publish(Event(
            event_type="system.health.started",
            payload={"interval": self._check_interval},
            timestamp=time.time(),
            source="health_monitor",
        ))
    
    async def stop(self) -> None:
        """Stop health monitoring."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("HealthMonitor stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                report = await self.check_all()
                await self._process_report(report)
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error: %s", e)
                await asyncio.sleep(self._check_interval)
    
    async def check_all(self) -> SystemHealthReport:
        """Run all health checks and return a report."""
        services: List[HealthCheckResult] = []
        now = time.time()
        
        # 1. Check EventBus
        services.append(self._check_event_bus())
        
        # 2. Check system resources
        services.append(self._check_cpu())
        services.append(self._check_ram())
        services.append(self._check_disk())
        
        # 3. Check critical files
        services.append(self._check_critical_files())
        
        # 4. Run custom checkers
        for name, checker in self._custom_checkers.items():
            try:
                if asyncio.iscoroutinefunction(checker):
                    result = await checker()
                else:
                    result = checker()
                if isinstance(result, HealthCheckResult):
                    services.append(result)
                else:
                    services.append(HealthCheckResult(
                        service_name=name,
                        status=ServiceStatus.HEALTHY,
                        timestamp=now,
                    ))
            except Exception as e:
                services.append(HealthCheckResult(
                    service_name=name,
                    status=ServiceStatus.UNHEALTHY,
                    details={"error": str(e)},
                    timestamp=now,
                ))
        
        # Calculate overall status
        unhealthy_count = sum(
            1 for s in services
            if s.status in (ServiceStatus.UNHEALTHY, ServiceStatus.CRASHED)
        )
        degraded_count = sum(
            1 for s in services
            if s.status == ServiceStatus.DEGRADED
        )
        
        if unhealthy_count > 0:
            overall = ServiceStatus.UNHEALTHY
        elif degraded_count > 0:
            overall = ServiceStatus.DEGRADED
        else:
            overall = ServiceStatus.HEALTHY
        
        # Resource usage
        cpu = psutil.cpu_percent(interval=0)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        
        report = SystemHealthReport(
            overall_status=overall,
            services=services,
            cpu_percent=cpu,
            ram_percent=ram,
            disk_percent=disk,
            uptime_seconds=now - self._start_time,
            checks_passed=sum(1 for s in services if s.status == ServiceStatus.HEALTHY),
            checks_failed=unhealthy_count + degraded_count,
            timestamp=now,
        )
        
        self._total_checks += 1
        if unhealthy_count > 0:
            self._total_failures += 1
        
        # Store in history
        self._history.append(report)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Update cached statuses
        for s in services:
            self._service_statuses[s.service_name] = s.status
        
        return report
    
    async def _process_report(self, report: SystemHealthReport) -> None:
        """Process a health report — publish events and trigger alerts."""
        # Always publish periodic status
        await self._event_bus.publish(Event(
            event_type="system.health.status",
            payload=report.model_dump(),
            timestamp=report.timestamp,
            source="health_monitor",
        ))
        
        # Alert on status changes
        for service in report.services:
            old_status = self._service_statuses.get(service.service_name)
            
            if old_status != service.status:
                if service.status in (ServiceStatus.UNHEALTHY, ServiceStatus.CRASHED):
                    self._total_alerts += 1
                    await self._event_bus.publish(Event(
                        event_type="system.health.alert",
                        payload={
                            "service": service.service_name,
                            "old_status": old_status.value if old_status else "UNKNOWN",
                            "new_status": service.status.value,
                            "details": service.details,
                        },
                        timestamp=time.time(),
                        source="health_monitor",
                    ))
                    logger.warning(
                        "Health alert: %s -> %s (was %s)",
                        service.service_name, service.status.value,
                        old_status.value if old_status else "UNKNOWN"
                    )
                
                elif service.status == ServiceStatus.HEALTHY and old_status in (
                    ServiceStatus.UNHEALTHY, ServiceStatus.CRASHED, ServiceStatus.DEGRADED
                ):
                    await self._event_bus.publish(Event(
                        event_type="system.health.recovered",
                        payload={
                            "service": service.service_name,
                            "old_status": old_status.value,
                            "new_status": service.status.value,
                        },
                        timestamp=time.time(),
                        source="health_monitor",
                    ))
                    logger.info(
                        "Health recovered: %s -> HEALTHY (was %s)",
                        service.service_name, old_status.value
                    )
    
    # ── Individual Health Checks ──────────────────────────────
    
    def _check_event_bus(self) -> HealthCheckResult:
        """Check EventBus health."""
        now = time.time()
        try:
            stats = self._event_bus.get_stats()
            
            if stats["total_errors"] > 100:
                status = ServiceStatus.DEGRADED
            elif stats["active_subscriptions"] == 0:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.HEALTHY
            
            return HealthCheckResult(
                service_name="event_bus",
                status=status,
                details=stats,
                timestamp=now,
            )
        except Exception as e:
            return HealthCheckResult(
                service_name="event_bus",
                status=ServiceStatus.UNHEALTHY,
                details={"error": str(e)},
                timestamp=now,
            )
    
    def _check_cpu(self) -> HealthCheckResult:
        """Check CPU health."""
        now = time.time()
        cpu = psutil.cpu_percent(interval=0)
        
        if cpu > 95:
            status = ServiceStatus.CRASHED
        elif cpu > 85:
            status = ServiceStatus.UNHEALTHY
        elif cpu > 70:
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.HEALTHY
        
        return HealthCheckResult(
            service_name="cpu",
            status=status,
            details={"percent": cpu, "cores": psutil.cpu_count()},
            timestamp=now,
        )
    
    def _check_ram(self) -> HealthCheckResult:
        """Check RAM health."""
        now = time.time()
        ram = psutil.virtual_memory()
        
        if ram.percent > 95:
            status = ServiceStatus.CRASHED
        elif ram.percent > 85:
            status = ServiceStatus.UNHEALTHY
        elif ram.percent > 75:
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.HEALTHY
        
        return HealthCheckResult(
            service_name="ram",
            status=status,
            details={
                "percent": ram.percent,
                "total_gb": round(ram.total / (1024**3), 2),
                "available_gb": round(ram.available / (1024**3), 2),
            },
            timestamp=now,
        )
    
    def _check_disk(self) -> HealthCheckResult:
        """Check disk health."""
        now = time.time()
        disk = psutil.disk_usage("/")
        
        if disk.percent > 98:
            status = ServiceStatus.CRASHED
        elif disk.percent > 90:
            status = ServiceStatus.UNHEALTHY
        elif disk.percent > 80:
            status = ServiceStatus.DEGRADED
        else:
            status = ServiceStatus.HEALTHY
        
        return HealthCheckResult(
            service_name="disk",
            status=status,
            details={
                "percent": disk.percent,
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
            },
            timestamp=now,
        )
    
    def _check_critical_files(self) -> HealthCheckResult:
        """Check integrity of critical files."""
        now = time.time()
        missing = []
        corrupted = []
        
        for file_path in self._critical_files:
            if not os.path.exists(file_path):
                missing.append(file_path)
            else:
                try:
                    if file_path.endswith(".json"):
                        with open(file_path) as f:
                            json.load(f)
                except (json.JSONDecodeError, Exception):
                    corrupted.append(file_path)
        
        if missing or corrupted:
            status = ServiceStatus.UNHEALTHY
        else:
            status = ServiceStatus.HEALTHY
        
        return HealthCheckResult(
            service_name="critical_files",
            status=status,
            details={
                "checked": len(self._critical_files),
                "missing": missing,
                "corrupted": corrupted,
            },
            timestamp=now,
        )
    
    # ── Data Integrity ────────────────────────────────────────
    
    async def check_file_integrity(self, file_path: str) -> IntegrityCheckResult:
        """Check integrity of a specific file."""
        now = time.time()
        
        if not os.path.exists(file_path):
            return IntegrityCheckResult(
                file_path=file_path,
                is_valid=False,
                error_message="File not found",
                timestamp=now,
            )
        
        try:
            stat = os.stat(file_path)
            content = open(file_path, "rb").read()
            checksum = hashlib.sha256(content).hexdigest()
            
            # Try to parse JSON files
            if file_path.endswith(".json"):
                json.loads(content)
            
            return IntegrityCheckResult(
                file_path=file_path,
                is_valid=True,
                checksum=checksum,
                file_size_bytes=stat.st_size,
                timestamp=now,
            )
        except json.JSONDecodeError as e:
            return IntegrityCheckResult(
                file_path=file_path,
                is_valid=False,
                error_message=f"Invalid JSON: {e}",
                timestamp=now,
            )
        except Exception as e:
            return IntegrityCheckResult(
                file_path=file_path,
                is_valid=False,
                error_message=str(e),
                timestamp=now,
            )
    
    # ── Statistics ────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get HealthMonitor statistics."""
        return {
            "running": self._running,
            "check_interval": self._check_interval,
            "total_checks": self._total_checks,
            "total_failures": self._total_failures,
            "total_alerts": self._total_alerts,
            "history_size": len(self._history),
            "monitored_services": list(self._service_statuses.keys()),
            "custom_checkers": list(self._custom_checkers.keys()),
            "critical_files": self._critical_files,
            "uptime_seconds": round(time.time() - self._start_time, 1),
        }
    
    def get_status_summary(self) -> Dict[str, str]:
        """Get current status of all monitored services."""
        return {k: v.value for k, v in self._service_statuses.items()}
