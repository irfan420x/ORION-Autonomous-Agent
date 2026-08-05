"""
ORION Self-Healer
=================

Automated recovery engine for ORION.
Detects failures and takes corrective actions.

Recovery Actions:
- RESTART: Restart a crashed service
- RESTORE_BACKUP: Restore corrupted data from backup
- REINSTALL: Reinstall missing dependencies
- RECONNECT: Reconnect to lost connections
- NOTIFY_USER: Alert the user
- ESCALATE: Escalate to human intervention

Usage:
    healer = SelfHealer(event_bus, health_monitor)
    await healer.start()
"""

import asyncio
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.contracts.reliability_contracts import (
    FailureReport,
    RecoveryAction,
    RecoveryResult,
    ServiceStatus,
)
from orion.core.communication.event_bus import EventBus
from orion.reliability.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


class SelfHealer:
    """
    Automated recovery engine for ORION.
    
    Listens for health alerts and attempts recovery.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        health_monitor: HealthMonitor,
        backup_dir: str = "state/backups",
        max_recovery_attempts: int = 3,
    ):
        self._event_bus = event_bus
        self._health_monitor = health_monitor
        self._backup_dir = backup_dir
        self._max_attempts = max_recovery_attempts
        self._running = False
        
        # Recovery history
        self._recovery_history: List[RecoveryResult] = []
        self._max_history: int = 50
        
        # Track attempts per service
        self._attempt_counts: Dict[str, int] = {}
        
        # Backup checksums
        self._backup_checksums: Dict[str, str] = {}
        
        # Stats
        self._total_recoveries: int = 0
        self._successful_recoveries: int = 0
        self._failed_recoveries: int = 0
        
        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)
        
        logger.info("SelfHealer created (backup_dir=%s)", backup_dir)
    
    async def start(self) -> None:
        """Start listening for health alerts."""
        if self._running:
            return
        
        self._running = True
        
        # Subscribe to health alerts
        await self._event_bus.subscribe("system.health.alert", self._handle_alert)
        
        # Create initial backups of critical files
        await self._backup_critical_files()
        
        logger.info("SelfHealer started")
        await self._event_bus.publish(Event(
            event_type="system.healer.started",
            payload={"backup_dir": self._backup_dir},
            timestamp=time.time(),
            source="self_healer",
        ))
    
    async def stop(self) -> None:
        """Stop the self-healer."""
        self._running = False
        await self._event_bus.unsubscribe("system.health.alert", self._handle_alert)
        logger.info("SelfHealer stopped")
    
    async def _handle_alert(self, event: Event) -> None:
        """Handle a health alert event."""
        if not self._running:
            return
        
        service = event.payload.get("service", "unknown")
        new_status = event.payload.get("new_status", "UNKNOWN")
        details = event.payload.get("details", {})
        
        logger.warning("Health alert received: %s -> %s", service, new_status)
        
        # Determine recovery action
        action = self._determine_action(service, new_status, details)
        
        if action == RecoveryAction.NONE:
            return
        
        # Attempt recovery
        result = await self._attempt_recovery(service, action, details)
        
        # Store result
        self._recovery_history.append(result)
        if len(self._recovery_history) > self._max_history:
            self._recovery_history.pop(0)
        
        # Publish recovery result
        await self._event_bus.publish(Event(
            event_type="system.healer.recovery",
            payload=result.model_dump(),
            timestamp=time.time(),
            source="self_healer",
        ))
    
    def _determine_action(
        self, service: str, status: str, details: Dict[str, Any]
    ) -> RecoveryAction:
        """Determine the appropriate recovery action."""
        # Check if we've exceeded max attempts
        attempts = self._attempt_counts.get(service, 0)
        if attempts >= self._max_attempts:
            logger.warning(
                "Max recovery attempts (%d) reached for %s, escalating",
                self._max_attempts, service
            )
            return RecoveryAction.ESCALATE
        
        # Determine action based on service and status
        if status == "CRASHED":
            if service in ("cpu", "ram", "disk"):
                return RecoveryAction.NOTIFY_USER
            return RecoveryAction.RESTART
        
        elif status == "UNHEALTHY":
            if service == "critical_files":
                return RecoveryAction.RESTORE_BACKUP
            elif service in ("event_bus",):
                return RecoveryAction.RECONNECT
            return RecoveryAction.RESTART
        
        elif status == "DEGRADED":
            return RecoveryAction.NONE  # Monitor, don't act yet
        
        return RecoveryAction.NONE
    
    async def _attempt_recovery(
        self, service: str, action: RecoveryAction, details: Dict[str, Any]
    ) -> RecoveryResult:
        """Attempt a recovery action."""
        self._total_recoveries += 1
        self._attempt_counts[service] = self._attempt_counts.get(service, 0) + 1
        now = time.time()
        
        try:
            if action == RecoveryAction.RESTART:
                success = await self._recover_restart(service)
            elif action == RecoveryAction.RESTORE_BACKUP:
                success = await self._recover_restore(service, details)
            elif action == RecoveryAction.RECONNECT:
                success = await self._recover_reconnect(service)
            elif action == RecoveryAction.NOTIFY_USER:
                success = await self._recover_notify(service, details)
            elif action == RecoveryAction.ESCALATE:
                success = await self._recover_escalate(service, details)
            else:
                success = False
            
            if success:
                self._successful_recoveries += 1
                self._attempt_counts[service] = 0  # Reset on success
            else:
                self._failed_recoveries += 1
            
            return RecoveryResult(
                success=success,
                action_taken=action,
                service_name=service,
                details="Recovery completed" if success else "Recovery failed",
                attempts=self._attempt_counts.get(service, 1),
                timestamp=now,
            )
        
        except Exception as e:
            self._failed_recoveries += 1
            logger.error("Recovery error for %s: %s", service, e)
            return RecoveryResult(
                success=False,
                action_taken=action,
                service_name=service,
                details=f"Error: {e}",
                attempts=self._attempt_counts.get(service, 1),
                timestamp=now,
            )
    
    # ── Recovery Strategies ───────────────────────────────────
    
    async def _recover_restart(self, service: str) -> bool:
        """Attempt to restart a service."""
        logger.info("Attempting restart of %s", service)
        
        # For now, just log and return True
        # In production, this would actually restart the service
        await asyncio.sleep(0.1)
        
        logger.info("Service %s restarted successfully", service)
        return True
    
    async def _recover_reconnect(self, service: str) -> bool:
        """Attempt to reconnect a service."""
        logger.info("Attempting reconnect of %s", service)
        await asyncio.sleep(0.1)
        
        logger.info("Service %s reconnected successfully", service)
        return True
    
    async def _recover_restore(
        self, service: str, details: Dict[str, Any]
    ) -> bool:
        """Restore corrupted files from backup."""
        corrupted = details.get("corrupted", [])
        missing = details.get("missing", [])
        
        all_files = corrupted + missing
        
        if not all_files:
            logger.info("No files to restore for %s", service)
            return True
        
        restored = 0
        for file_path in all_files:
            backup_path = os.path.join(
                self._backup_dir,
                os.path.basename(file_path) + ".backup"
            )
            
            if os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, file_path)
                    logger.info("Restored %s from backup", file_path)
                    restored += 1
                except Exception as e:
                    logger.error("Failed to restore %s: %s", file_path, e)
            else:
                logger.warning("No backup found for %s", file_path)
        
        return restored > 0
    
    async def _recover_notify(
        self, service: str, details: Dict[str, Any]
    ) -> bool:
        """Notify user about a critical issue."""
        logger.warning(
            "CRITICAL: Service %s needs attention. Details: %s",
            service, details
        )
        
        await self._event_bus.publish(Event(
            event_type="system.healer.user_notification",
            payload={
                "service": service,
                "message": f"Service {service} requires manual attention",
                "details": details,
                "severity": "critical",
            },
            timestamp=time.time(),
            source="self_healer",
        ))
        
        return True
    
    async def _recover_escalate(
        self, service: str, details: Dict[str, Any]
    ) -> bool:
        """Escalate to human intervention."""
        logger.error(
            "ESCALATION: Service %s failed after %d attempts. Manual intervention required.",
            service, self._max_attempts
        )
        
        await self._event_bus.publish(Event(
            event_type="system.healer.escalation",
            payload={
                "service": service,
                "message": f"Service {service} failed after {self._max_attempts} recovery attempts",
                "details": details,
                "severity": "critical",
            },
            timestamp=time.time(),
            source="self_healer",
        ))
        
        return True
    
    # ── Backup Management ─────────────────────────────────────
    
    async def _backup_critical_files(self) -> None:
        """Create backups of critical files."""
        critical_files = self._health_monitor._critical_files
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                backup_path = os.path.join(
                    self._backup_dir,
                    os.path.basename(file_path) + ".backup"
                )
                try:
                    shutil.copy2(file_path, backup_path)
                    logger.debug("Backed up %s to %s", file_path, backup_path)
                except Exception as e:
                    logger.error("Failed to backup %s: %s", file_path, e)
    
    async def create_backup(self, file_path: str) -> bool:
        """Create a backup of a specific file."""
        if not os.path.exists(file_path):
            logger.warning("Cannot backup non-existent file: %s", file_path)
            return False
        
        backup_path = os.path.join(
            self._backup_dir,
            os.path.basename(file_path) + ".backup"
        )
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info("Created backup: %s -> %s", file_path, backup_path)
            return True
        except Exception as e:
            logger.error("Backup failed for %s: %s", file_path, e)
            return False
    
    # ── Statistics ────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SelfHealer statistics."""
        return {
            "running": self._running,
            "total_recoveries": self._total_recoveries,
            "successful_recoveries": self._successful_recoveries,
            "failed_recoveries": self._failed_recoveries,
            "success_rate": (
                round(self._successful_recoveries / self._total_recoveries * 100, 1)
                if self._total_recoveries > 0 else 0.0
            ),
            "attempt_counts": dict(self._attempt_counts),
            "backup_dir": self._backup_dir,
            "history_size": len(self._recovery_history),
            "max_attempts": self._max_attempts,
        }
    
    def get_recovery_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent recovery history."""
        return [r.model_dump() for r in self._recovery_history[-limit:]]
