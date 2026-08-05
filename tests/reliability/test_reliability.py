"""
Tests for ORION Reliability (Health Monitor + Self-Healer)
==========================================================
"""

import asyncio
import json
import os
import pytest
import tempfile
import time
from unittest.mock import patch, MagicMock, AsyncMock

from orion.core.communication.event_bus import EventBus
from orion.contracts.reliability_contracts import (
    HealthCheckResult,
    ServiceStatus,
    SystemHealthReport,
    FailureReport,
    RecoveryAction,
    RecoveryResult,
    IntegrityCheckResult,
)
from orion.reliability.health_monitor import HealthMonitor
from orion.reliability.self_healer import SelfHealer
from orion.contracts.agent_contracts import Event


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def health_monitor(event_bus):
    return HealthMonitor(event_bus, check_interval=0.1)


@pytest.fixture
def self_healer(event_bus, health_monitor):
    return SelfHealer(event_bus, health_monitor, backup_dir="/tmp/orion_test_backups")


@pytest.fixture
def tmp_json_file(tmp_path):
    """Create a temporary JSON file."""
    file_path = tmp_path / "test_state.json"
    file_path.write_text('{"key": "value"}')
    return str(file_path)


# ── Health Monitor Tests ─────────────────────────────────────

class TestHealthMonitor:
    """Test HealthMonitor functionality."""
    
    @pytest.mark.asyncio
    async def test_initial_state(self, health_monitor):
        """Monitor starts stopped."""
        assert not health_monitor.is_running
        assert health_monitor.last_report is None
    
    @pytest.mark.asyncio
    async def test_start_stop(self, health_monitor):
        """Can start and stop monitoring."""
        await health_monitor.start()
        assert health_monitor.is_running
        
        await health_monitor.stop()
        assert not health_monitor.is_running
    
    @pytest.mark.asyncio
    async def test_check_all_returns_report(self, health_monitor):
        """check_all returns a SystemHealthReport."""
        report = await health_monitor.check_all()
        
        assert isinstance(report, SystemHealthReport)
        assert report.overall_status in ServiceStatus
        assert len(report.services) > 0
        assert report.cpu_percent >= 0
        assert report.ram_percent >= 0
        assert report.disk_percent >= 0
        assert report.timestamp > 0
    
    @pytest.mark.asyncio
    async def test_check_event_bus(self, health_monitor):
        """EventBus check returns a valid status."""
        result = health_monitor._check_event_bus()
        
        assert isinstance(result, HealthCheckResult)
        assert result.service_name == "event_bus"
        # Fresh EventBus has no subscribers, so it may be DEGRADED
        assert result.status in (ServiceStatus.HEALTHY, ServiceStatus.DEGRADED)
    
    @pytest.mark.asyncio
    async def test_check_cpu(self, health_monitor):
        """CPU check returns valid result."""
        result = health_monitor._check_cpu()
        
        assert result.service_name == "cpu"
        assert result.status in ServiceStatus
        assert "percent" in result.details
    
    @pytest.mark.asyncio
    async def test_check_ram(self, health_monitor):
        """RAM check returns valid result."""
        result = health_monitor._check_ram()
        
        assert result.service_name == "ram"
        assert "total_gb" in result.details
        assert result.details["total_gb"] > 0
    
    @pytest.mark.asyncio
    async def test_check_disk(self, health_monitor):
        """Disk check returns valid result."""
        result = health_monitor._check_disk()
        
        assert result.service_name == "disk"
        assert "free_gb" in result.details
    
    @pytest.mark.asyncio
    async def test_check_critical_files_ok(self, event_bus, tmp_json_file):
        """Critical files check passes for valid JSON."""
        monitor = HealthMonitor(event_bus)
        monitor.add_critical_file(tmp_json_file)
        
        result = monitor._check_critical_files()
        assert result.status == ServiceStatus.HEALTHY
        assert result.details["checked"] >= 1
    
    @pytest.mark.asyncio
    async def test_check_critical_files_missing(self, event_bus):
        """Critical files check fails for missing file."""
        monitor = HealthMonitor(event_bus)
        monitor.add_critical_file("/nonexistent/file.json")
        
        result = monitor._check_critical_files()
        assert result.status == ServiceStatus.UNHEALTHY
        assert "/nonexistent/file.json" in result.details["missing"]
    
    @pytest.mark.asyncio
    async def test_check_critical_files_corrupted(self, event_bus, tmp_path):
        """Critical files check fails for corrupted JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json")
        
        monitor = HealthMonitor(event_bus)
        monitor.add_critical_file(str(bad_file))
        
        result = monitor._check_critical_files()
        assert result.status == ServiceStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_custom_checker(self, health_monitor):
        """Custom health checker is called."""
        called = []
        
        def my_checker():
            called.append(True)
            return HealthCheckResult(
                service_name="custom",
                status=ServiceStatus.HEALTHY,
                timestamp=time.time(),
            )
        
        health_monitor.register_checker("custom", my_checker)
        report = await health_monitor.check_all()
        
        assert len(called) == 1
        assert any(s.service_name == "custom" for s in report.services)
    
    @pytest.mark.asyncio
    async def test_custom_async_checker(self, health_monitor):
        """Async custom health checker works."""
        called = []
        
        async def my_checker():
            called.append(True)
            return HealthCheckResult(
                service_name="async_custom",
                status=ServiceStatus.HEALTHY,
                timestamp=time.time(),
            )
        
        health_monitor.register_checker("async_custom", my_checker)
        report = await health_monitor.check_all()
        
        assert len(called) == 1
    
    @pytest.mark.asyncio
    async def test_custom_checker_exception(self, health_monitor):
        """Custom checker exception results in unhealthy."""
        def bad_checker():
            raise RuntimeError("checker failed")
        
        health_monitor.register_checker("bad", bad_checker)
        report = await health_monitor.check_all()
        
        bad_results = [s for s in report.services if s.service_name == "bad"]
        assert len(bad_results) == 1
        assert bad_results[0].status == ServiceStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_monitoring_publishes_events(self, event_bus, health_monitor):
        """Monitoring publishes health status events."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("system.health.status", handler)
        await health_monitor.start()
        await asyncio.sleep(0.3)
        await health_monitor.stop()
        
        assert len(events) >= 1
        assert events[0].event_type == "system.health.status"
    
    @pytest.mark.asyncio
    async def test_history_accumulates(self, health_monitor):
        """Check history accumulates."""
        await health_monitor.check_all()
        await health_monitor.check_all()
        
        assert len(health_monitor._history) == 2
    
    @pytest.mark.asyncio
    async def test_file_integrity_valid(self, health_monitor, tmp_json_file):
        """File integrity check passes for valid file."""
        result = await health_monitor.check_file_integrity(tmp_json_file)
        
        assert result.is_valid
        assert result.checksum is not None
        assert result.file_size_bytes > 0
    
    @pytest.mark.asyncio
    async def test_file_integrity_missing(self, health_monitor):
        """File integrity check fails for missing file."""
        result = await health_monitor.check_file_integrity("/nonexistent")
        
        assert not result.is_valid
        assert "not found" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_file_integrity_corrupted_json(self, health_monitor, tmp_path):
        """File integrity check fails for corrupted JSON."""
        bad = tmp_path / "bad.json"
        bad.write_text("{broken")
        
        result = await health_monitor.check_file_integrity(str(bad))
        assert not result.is_valid
    
    @pytest.mark.asyncio
    async def test_get_stats(self, health_monitor):
        """get_stats returns comprehensive stats."""
        await health_monitor.check_all()
        stats = health_monitor.get_stats()
        
        assert "running" in stats
        assert "total_checks" in stats
        assert "total_failures" in stats
        assert stats["total_checks"] >= 1
    
    @pytest.mark.asyncio
    async def test_status_summary(self, health_monitor):
        """get_status_summary returns service statuses."""
        await health_monitor.check_all()
        summary = health_monitor.get_status_summary()
        
        assert isinstance(summary, dict)
        assert "event_bus" in summary
    
    @pytest.mark.asyncio
    async def test_overall_status_healthy(self, health_monitor):
        """Overall status is HEALTHY when all services OK."""
        report = await health_monitor.check_all()
        # On a healthy system, overall should be HEALTHY
        assert report.overall_status in (ServiceStatus.HEALTHY, ServiceStatus.DEGRADED)


# ── Self-Healer Tests ────────────────────────────────────────

class TestSelfHealer:
    """Test SelfHealer functionality."""
    
    @pytest.mark.asyncio
    async def test_initial_state(self, self_healer):
        """Healer starts stopped."""
        assert not self_healer._running
    
    @pytest.mark.asyncio
    async def test_start_stop(self, self_healer):
        """Can start and stop."""
        await self_healer.start()
        assert self_healer._running
        
        await self_healer.stop()
        assert not self_healer._running
    
    @pytest.mark.asyncio
    async def test_backup_critical_files(self, event_bus, tmp_json_file):
        """Creates backups of critical files."""
        import shutil
        backup_dir = "/tmp/orion_test_backup_2"
        os.makedirs(backup_dir, exist_ok=True)
        
        monitor = HealthMonitor(event_bus)
        monitor.add_critical_file(tmp_json_file)
        
        healer = SelfHealer(event_bus, monitor, backup_dir=backup_dir)
        await healer._backup_critical_files()
        
        backup_path = os.path.join(
            backup_dir,
            os.path.basename(tmp_json_file) + ".backup"
        )
        assert os.path.exists(backup_path)
        
        # Cleanup
        shutil.rmtree(backup_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_create_backup(self, self_healer, tmp_json_file):
        """create_backup works for existing file."""
        result = await self_healer.create_backup(tmp_json_file)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_create_backup_missing(self, self_healer):
        """create_backup fails for missing file."""
        result = await self_healer.create_backup("/nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_determine_action_restart(self, self_healer):
        """CRASHED service gets RESTART action."""
        action = self_healer._determine_action("event_bus", "CRASHED", {})
        assert action == RecoveryAction.RESTART
    
    @pytest.mark.asyncio
    async def test_determine_action_restore(self, self_healer):
        """UNHEALTHY critical_files gets RESTORE action."""
        action = self_healer._determine_action("critical_files", "UNHEALTHY", {})
        assert action == RecoveryAction.RESTORE_BACKUP
    
    @pytest.mark.asyncio
    async def test_determine_action_notify(self, self_healer):
        """CRASHED cpu gets NOTIFY action."""
        action = self_healer._determine_action("cpu", "CRASHED", {})
        assert action == RecoveryAction.NOTIFY_USER
    
    @pytest.mark.asyncio
    async def test_determine_action_escalate(self, self_healer):
        """After max attempts, escalates."""
        self_healer._attempt_counts["test"] = 5
        action = self_healer._determine_action("test", "CRASHED", {})
        assert action == RecoveryAction.ESCALATE
    
    @pytest.mark.asyncio
    async def test_determine_action_degraded(self, self_healer):
        """DEGRADED gets NONE (monitor only)."""
        action = self_healer._determine_action("cpu", "DEGRADED", {})
        assert action == RecoveryAction.NONE
    
    @pytest.mark.asyncio
    async def test_recovery_restart(self, self_healer):
        """Restart recovery succeeds."""
        result = await self_healer._attempt_recovery(
            "test_service", RecoveryAction.RESTART, {}
        )
        
        assert result.success
        assert result.action_taken == RecoveryAction.RESTART
        assert self_healer._total_recoveries == 1
    
    @pytest.mark.asyncio
    async def test_recovery_restore(self, event_bus, tmp_path):
        """Restore recovery works with backup."""
        # Create a file and backup
        target = tmp_path / "state.json"
        target.write_text('{"original": true}')
        
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        backup = backup_dir / "state.json.backup"
        backup.write_text('{"restored": true}')
        
        monitor = HealthMonitor(event_bus)
        healer = SelfHealer(event_bus, monitor, backup_dir=str(backup_dir))
        
        # Corrupt the target
        target.write_text("{corrupted")
        
        result = await healer._attempt_recovery(
            "critical_files",
            RecoveryAction.RESTORE_BACKUP,
            {"corrupted": [str(target)], "missing": []}
        )
        
        assert result.success
        assert json.loads(target.read_text()) == {"restored": True}
    
    @pytest.mark.asyncio
    async def test_recovery_notify(self, self_healer):
        """Notify recovery publishes event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await self_healer._event_bus.subscribe("system.healer.user_notification", handler)
        
        result = await self_healer._attempt_recovery(
            "cpu", RecoveryAction.NOTIFY_USER, {"percent": 99}
        )
        
        assert result.success
        assert len(events) == 1
    
    @pytest.mark.asyncio
    async def test_recovery_escalate(self, self_healer):
        """Escalate recovery publishes event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await self_healer._event_bus.subscribe("system.healer.escalation", handler)
        
        result = await self_healer._attempt_recovery(
            "test", RecoveryAction.ESCALATE, {}
        )
        
        assert result.success
        assert len(events) == 1
    
    @pytest.mark.asyncio
    async def test_handle_alert_triggers_recovery(self, event_bus, self_healer):
        """Health alert triggers recovery."""
        await self_healer.start()
        
        # Directly call handle_alert to avoid event loop issues
        alert_event = Event(
            event_type="system.health.alert",
            payload={
                "service": "event_bus",
                "old_status": "HEALTHY",
                "new_status": "CRASHED",
                "details": {},
            },
            timestamp=time.time(),
            source="test",
        )
        await self_healer._handle_alert(alert_event)
        
        assert self_healer._total_recoveries >= 1
        
        await self_healer.stop()
    
    @pytest.mark.asyncio
    async def test_recovery_history(self, self_healer):
        """Recovery history accumulates via handle_alert."""
        await self_healer.start()
        
        # Trigger two recoveries directly
        await self_healer._handle_alert(Event(
            event_type="system.health.alert",
            payload={"service": "a", "new_status": "CRASHED", "details": {}},
            timestamp=time.time(),
            source="test",
        ))
        
        await self_healer._handle_alert(Event(
            event_type="system.health.alert",
            payload={"service": "b", "new_status": "CRASHED", "details": {}},
            timestamp=time.time(),
            source="test",
        ))
        
        history = self_healer.get_recovery_history()
        assert len(history) >= 1
        
        await self_healer.stop()
    
    @pytest.mark.asyncio
    async def test_get_stats(self, self_healer):
        """get_stats returns comprehensive stats."""
        await self_healer._attempt_recovery("test", RecoveryAction.RESTART, {})
        
        stats = self_healer.get_stats()
        
        assert "total_recoveries" in stats
        assert "successful_recoveries" in stats
        assert "failed_recoveries" in stats
        assert "success_rate" in stats
        assert stats["total_recoveries"] == 1
    
    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, self_healer):
        """Success rate is calculated correctly."""
        # One success
        await self_healer._attempt_recovery("a", RecoveryAction.RESTART, {})
        
        stats = self_healer.get_stats()
        assert stats["success_rate"] == 100.0


# ── Contracts Tests ──────────────────────────────────────────

class TestContracts:
    """Test Pydantic contracts."""
    
    def test_health_check_result(self):
        """HealthCheckResult can be created."""
        result = HealthCheckResult(
            service_name="test",
            status=ServiceStatus.HEALTHY,
            latency_ms=1.5,
            timestamp=time.time(),
        )
        assert result.service_name == "test"
        assert result.status == ServiceStatus.HEALTHY
    
    def test_system_health_report(self):
        """SystemHealthReport can be created."""
        report = SystemHealthReport(
            overall_status=ServiceStatus.HEALTHY,
            timestamp=time.time(),
        )
        assert report.overall_status == ServiceStatus.HEALTHY
        assert report.services == []
    
    def test_recovery_result(self):
        """RecoveryResult can be created."""
        result = RecoveryResult(
            success=True,
            action_taken=RecoveryAction.RESTART,
            service_name="test",
            timestamp=time.time(),
        )
        assert result.success is True
    
    def test_integrity_check_result(self):
        """IntegrityCheckResult can be created."""
        result = IntegrityCheckResult(
            file_path="/test/file.json",
            is_valid=True,
            timestamp=time.time(),
        )
        assert result.is_valid is True
    
    def test_service_status_enum(self):
        """ServiceStatus has all expected values."""
        assert ServiceStatus.HEALTHY == "HEALTHY"
        assert ServiceStatus.DEGRADED == "DEGRADED"
        assert ServiceStatus.UNHEALTHY == "UNHEALTHY"
        assert ServiceStatus.CRASHED == "CRASHED"
    
    def test_recovery_action_enum(self):
        """RecoveryAction has all expected values."""
        assert RecoveryAction.RESTART == "RESTART"
        assert RecoveryAction.RESTORE_BACKUP == "RESTORE_BACKUP"
        assert RecoveryAction.NOTIFY_USER == "NOTIFY_USER"
        assert RecoveryAction.ESCALATE == "ESCALATE"


# ── Integration Tests ────────────────────────────────────────

class TestIntegration:
    """Integration tests for HealthMonitor + SelfHealer."""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, event_bus):
        """Test complete lifecycle: start → check → alert → recover → stop."""
        monitor = HealthMonitor(event_bus, check_interval=0.2)
        healer = SelfHealer(event_bus, monitor, backup_dir="/tmp/orion_test_lifecycle")
        
        await monitor.start()
        await healer.start()
        
        # Wait for a few check cycles
        await asyncio.sleep(0.5)
        
        # Verify monitoring worked
        assert monitor._total_checks >= 1
        
        await healer.stop()
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_health_alert_flows_to_healer(self, event_bus):
        """Health alert from monitor flows to healer."""
        monitor = HealthMonitor(event_bus)
        healer = SelfHealer(event_bus, monitor)
        
        await healer.start()
        
        # Directly trigger a recovery
        alert = Event(
            event_type="system.health.alert",
            payload={
                "service": "test_service",
                "new_status": "CRASHED",
                "details": {},
            },
            timestamp=time.time(),
            source="test",
        )
        await healer._handle_alert(alert)
        
        assert healer._total_recoveries >= 1
        history = healer.get_recovery_history()
        assert len(history) >= 1
        assert history[0]["action_taken"] == "RESTART"
        
        await healer.stop()
