"""
Tests for ORION Adaptive Runtime
=================================
"""

import asyncio
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock

from orion.core.runtime.runtime import (
    AdaptiveRuntime,
    ResourceThreshold,
    ModulePriority,
    MODULE_PRIORITIES,
    MODE_THRESHOLDS,
)
from orion.core.communication.event_bus import EventBus
from orion.contracts.runtime_contracts import HardwareProfile


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def event_bus():
    """Create a fresh EventBus for each test."""
    return EventBus()


@pytest.fixture
def runtime(event_bus):
    """Create an AdaptiveRuntime instance."""
    return AdaptiveRuntime(event_bus)


@pytest.fixture
def mock_hardware():
    """Create a mock hardware profile."""
    return HardwareProfile(
        cpu_cores=8,
        total_ram_gb=16.0,
        has_gpu=True,
        gpu_model="NVIDIA RTX 3080",
        internet_connected=True,
        os_name="Linux",
        os_version="6.1.0",
    )


@pytest.fixture
def low_end_hardware():
    """Create a low-end hardware profile."""
    return HardwareProfile(
        cpu_cores=2,
        total_ram_gb=2.0,
        has_gpu=False,
        gpu_model=None,
        internet_connected=True,
        os_name="Linux",
        os_version="6.1.0",
    )


# ── Initialization Tests ────────────────────────────────────

class TestInitialization:
    """Test AdaptiveRuntime initialization."""
    
    @pytest.mark.asyncio
    async def test_initial_state(self, runtime):
        """Runtime starts uninitialized."""
        assert not runtime.is_initialized
        assert runtime.hardware_profile is None
        assert runtime.current_mode == "safe"
        assert not runtime.is_monitoring
    
    @pytest.mark.asyncio
    async def test_initialize_detects_hardware(self, runtime):
        """Initialize should detect hardware and set profile."""
        await runtime.initialize()
        
        assert runtime.is_initialized
        assert runtime.hardware_profile is not None
        assert runtime.hardware_profile.cpu_cores > 0
        assert runtime.hardware_profile.total_ram_gb > 0
        assert runtime.hardware_profile.os_name in ("Linux", "Windows", "Darwin")
    
    @pytest.mark.asyncio
    async def test_initialize_negotiates_mode(self, runtime):
        """Initialize should negotiate an operating mode."""
        await runtime.initialize()
        
        assert runtime.current_mode in ("full", "cpu_only", "low_memory", "offline", "server", "safe")
    
    @pytest.mark.asyncio
    async def test_initialize_starts_monitoring(self, runtime):
        """Initialize should start resource monitoring."""
        await runtime.initialize()
        
        assert runtime.is_monitoring
        
        # Cleanup
        await runtime.shutdown()
        assert not runtime.is_monitoring
    
    @pytest.mark.asyncio
    async def test_initialize_with_preferred_mode(self, runtime):
        """Initialize with preferred mode should use that mode."""
        await runtime.initialize(preferred_mode="cpu_only")
        
        assert runtime.current_mode == "cpu_only"
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialize_publishes_event(self, event_bus, runtime):
        """Initialize should publish system.runtime.initialized event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("system.runtime.initialized", handler)
        await runtime.initialize()
        
        assert len(events) == 1
        assert events[0].event_type == "system.runtime.initialized"
        assert "hardware_profile" in events[0].payload
        assert "operating_mode" in events[0].payload
        
        await runtime.shutdown()


# ── Hardware Detection Tests ────────────────────────────────

class TestHardwareDetection:
    """Test hardware detection."""
    
    @pytest.mark.asyncio
    async def test_hardware_profile_fields(self, runtime):
        """Hardware profile should have all required fields."""
        await runtime.initialize()
        profile = runtime.hardware_profile
        
        assert hasattr(profile, 'cpu_cores')
        assert hasattr(profile, 'total_ram_gb')
        assert hasattr(profile, 'has_gpu')
        assert hasattr(profile, 'internet_connected')
        assert hasattr(profile, 'os_name')
        assert hasattr(profile, 'os_version')
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_cpu_cores_positive(self, runtime):
        """CPU cores should be a positive integer."""
        await runtime.initialize()
        assert runtime.hardware_profile.cpu_cores >= 1
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_ram_positive(self, runtime):
        """Total RAM should be positive."""
        await runtime.initialize()
        assert runtime.hardware_profile.total_ram_gb > 0
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_hardware_event_published(self, event_bus, runtime):
        """Hardware detection should publish system.hardware_profile event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("system.hardware_profile", handler)
        await runtime.initialize()
        
        assert len(events) >= 1
        hw_events = [e for e in events if e.event_type == "system.hardware_profile"]
        assert len(hw_events) == 1
        
        await runtime.shutdown()


# ── Mode Negotiation Tests ──────────────────────────────────

class TestModeNegotiation:
    """Test operating mode negotiation logic."""
    
    def test_negotiate_full_mode(self, runtime, mock_hardware):
        """High-end hardware with GPU should negotiate 'full' mode."""
        mode = runtime._negotiate_mode(mock_hardware)
        assert mode == "full"
    
    def test_negotiate_cpu_only_mode(self, runtime):
        """Hardware with good RAM but no GPU should negotiate 'cpu_only'."""
        profile = HardwareProfile(
            cpu_cores=4, total_ram_gb=8.0, has_gpu=False,
            gpu_model=None, internet_connected=True,
            os_name="Linux", os_version="6.1.0"
        )
        mode = runtime._negotiate_mode(profile)
        assert mode == "cpu_only"
    
    def test_negotiate_low_memory_mode(self, runtime, low_end_hardware):
        """Low RAM should negotiate 'low_memory' mode."""
        mode = runtime._negotiate_mode(low_end_hardware)
        assert mode == "low_memory"
    
    def test_negotiate_offline_mode(self, runtime):
        """No internet should negotiate 'offline' mode."""
        profile = HardwareProfile(
            cpu_cores=4, total_ram_gb=8.0, has_gpu=False,
            gpu_model=None, internet_connected=False,
            os_name="Linux", os_version="6.1.0"
        )
        mode = runtime._negotiate_mode(profile)
        assert mode == "offline"
    
    def test_is_mode_feasible_full(self, runtime, mock_hardware):
        """Full mode should be feasible on high-end hardware."""
        runtime._hardware_profile = mock_hardware
        assert runtime._is_mode_feasible("full")
    
    def test_is_mode_feasible_low_ram(self, runtime, low_end_hardware):
        """Full mode should NOT be feasible on low-end hardware."""
        runtime._hardware_profile = low_end_hardware
        assert not runtime._is_mode_feasible("full")
    
    def test_safe_mode_always_feasible(self, runtime, low_end_hardware):
        """Safe mode should always be feasible."""
        runtime._hardware_profile = low_end_hardware
        assert runtime._is_mode_feasible("safe")
    
    def test_get_feasible_modes(self, runtime, mock_hardware):
        """Should return list of feasible modes."""
        runtime._hardware_profile = mock_hardware
        modes = runtime.get_feasible_modes()
        assert isinstance(modes, list)
        assert "safe" in modes
        assert "full" in modes


# ── Mode Switching Tests ────────────────────────────────────

class TestModeSwitching:
    """Test operating mode switching."""
    
    @pytest.mark.asyncio
    async def test_switch_mode(self, runtime):
        """Should switch operating mode."""
        await runtime.initialize(preferred_mode="cpu_only")
        
        result = await runtime.switch_mode("low_memory", reason="test")
        
        assert result is True
        assert runtime.current_mode == "low_memory"
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_switch_same_mode(self, runtime):
        """Switching to same mode should return True without change."""
        await runtime.initialize(preferred_mode="cpu_only")
        
        result = await runtime.switch_mode("cpu_only")
        
        assert result is True
        assert runtime.current_mode == "cpu_only"
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_switch_infeasible_mode(self, runtime, low_end_hardware):
        """Switching to infeasible mode should return False."""
        runtime._hardware_profile = low_end_hardware
        runtime._current_mode = "low_memory"
        runtime._initialized = True
        
        result = await runtime.switch_mode("full")
        
        assert result is False
        assert runtime.current_mode == "low_memory"
    
    @pytest.mark.asyncio
    async def test_switch_publishes_event(self, event_bus, runtime):
        """Mode switch should publish system.operating_mode.changed event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("system.operating_mode.changed", handler)
        await runtime.initialize(preferred_mode="cpu_only")
        
        await runtime.switch_mode("low_memory", reason="test_switch")
        
        mode_events = [e for e in events if e.event_type == "system.operating_mode.changed"]
        assert len(mode_events) >= 1
        assert mode_events[-1].payload["old_mode"] == "cpu_only"
        assert mode_events[-1].payload["new_mode"] == "low_memory"
        assert mode_events[-1].payload["reason"] == "test_switch"
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_mode_switch_counter(self, runtime):
        """Mode switches should be counted."""
        await runtime.initialize(preferred_mode="cpu_only")
        
        await runtime.switch_mode("low_memory")
        await runtime.switch_mode("safe")
        
        assert runtime._mode_switches == 2
        
        await runtime.shutdown()


# ── Module Management Tests ─────────────────────────────────

class TestModuleManagement:
    """Test module loading/unloading based on mode."""
    
    @pytest.mark.asyncio
    async def test_full_mode_loads_all(self, runtime):
        """Full mode should load all modules."""
        await runtime.initialize(preferred_mode="full")
        
        assert runtime.is_module_loaded("event_bus")
        assert runtime.is_module_loaded("local_llm")
        assert runtime.is_module_loaded("vision_engine")
        assert runtime.is_module_loaded("browser")
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_low_memory_only_critical_high(self, runtime):
        """Low memory mode should only load critical and high modules."""
        await runtime.initialize(preferred_mode="low_memory")
        
        assert runtime.is_module_loaded("event_bus")  # CRITICAL
        assert runtime.is_module_loaded("memory")     # HIGH
        assert not runtime.is_module_loaded("local_llm")  # LOW
        assert not runtime.is_module_loaded("vision_engine")  # MEDIUM
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_safe_mode_only_critical(self, runtime):
        """Safe mode should only load critical modules."""
        await runtime.initialize(preferred_mode="safe")
        
        assert runtime.is_module_loaded("event_bus")  # CRITICAL
        assert runtime.is_module_loaded("state_machine")  # CRITICAL
        assert not runtime.is_module_loaded("memory")  # HIGH
        assert not runtime.is_module_loaded("browser")  # MEDIUM
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_cpu_only_skips_local_llm(self, runtime):
        """CPU-only mode should skip local LLM."""
        await runtime.initialize(preferred_mode="cpu_only")
        
        assert not runtime.is_module_loaded("local_llm")
        assert runtime.is_module_loaded("vision_engine")
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_module_priority_lookup(self, runtime):
        """Should be able to look up module priorities."""
        assert runtime.get_module_priority("event_bus") == ModulePriority.CRITICAL
        assert runtime.get_module_priority("memory") == ModulePriority.HIGH
        assert runtime.get_module_priority("vision_engine") == ModulePriority.MEDIUM
        assert runtime.get_module_priority("local_llm") == ModulePriority.LOW
        assert runtime.get_module_priority("nonexistent") is None
    
    @pytest.mark.asyncio
    async def test_loaded_modules_is_copy(self, runtime):
        """loaded_modules property should return a copy."""
        await runtime.initialize()
        mods = runtime.loaded_modules
        mods.add("fake_module")
        assert not runtime.is_module_loaded("fake_module")
        await runtime.shutdown()


# ── Resource Monitoring Tests ───────────────────────────────

class TestResourceMonitoring:
    """Test resource monitoring."""
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, runtime):
        """Should be able to start and stop monitoring."""
        await runtime.start_monitoring(interval_seconds=0.1)
        assert runtime.is_monitoring
        
        await asyncio.sleep(0.2)
        
        await runtime.stop_monitoring()
        assert not runtime.is_monitoring
    
    @pytest.mark.asyncio
    async def test_resource_usage_snapshot(self, runtime):
        """get_resource_usage should return current resource data."""
        usage = runtime.get_resource_usage()
        
        assert "cpu" in usage
        assert "ram" in usage
        assert "disk" in usage
        
        assert "percent" in usage["cpu"]
        assert "cores" in usage["cpu"]
        assert "total_gb" in usage["ram"]
        assert "available_gb" in usage["ram"]
        assert "total_gb" in usage["disk"]
        assert "free_gb" in usage["disk"]
    
    @pytest.mark.asyncio
    async def test_threshold_classification(self):
        """Threshold classification should work correctly."""
        assert AdaptiveRuntime._get_threshold(30) == ResourceThreshold.LOW
        assert AdaptiveRuntime._get_threshold(60) == ResourceThreshold.MODERATE
        assert AdaptiveRuntime._get_threshold(80) == ResourceThreshold.HIGH
        assert AdaptiveRuntime._get_threshold(95) == ResourceThreshold.CRITICAL
    
    @pytest.mark.asyncio
    async def test_cpu_trend_empty(self, runtime):
        """CPU trend with no data should return zeros."""
        trend = runtime.get_cpu_trend()
        assert trend["samples"] == 0
        assert trend["avg"] == 0
    
    @pytest.mark.asyncio
    async def test_ram_trend_empty(self, runtime):
        """RAM trend with no data should return zeros."""
        trend = runtime.get_ram_trend()
        assert trend["samples"] == 0
        assert trend["avg"] == 0
    
    @pytest.mark.asyncio
    async def test_monitoring_populates_history(self, runtime):
        """Monitoring should populate resource history."""
        await runtime.start_monitoring(interval_seconds=0.1)
        await asyncio.sleep(0.3)
        await runtime.stop_monitoring()
        
        assert len(runtime._cpu_history) > 0
        assert len(runtime._ram_history) > 0
        
        trend = runtime.get_cpu_trend()
        assert trend["samples"] > 0
    
    @pytest.mark.asyncio
    async def test_history_max_size(self, runtime):
        """History should be capped at max_history."""
        runtime._max_history = 5
        for i in range(10):
            runtime._cpu_history.append(float(i))
            runtime._ram_history.append(float(i))
        
        # Simulate the trimming that happens in _check_resources
        while len(runtime._cpu_history) > runtime._max_history:
            runtime._cpu_history.pop(0)
        while len(runtime._ram_history) > runtime._max_history:
            runtime._ram_history.pop(0)
        
        assert len(runtime._cpu_history) == 5
        assert runtime._cpu_history[0] == 5.0  # Oldest kept


# ── Statistics Tests ────────────────────────────────────────

class TestStatistics:
    """Test statistics and reporting."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, runtime):
        """get_stats should return comprehensive stats."""
        await runtime.initialize()
        
        stats = runtime.get_stats()
        
        assert "initialized" in stats
        assert "monitoring" in stats
        assert "current_mode" in stats
        assert "mode_switches" in stats
        assert "resource_alerts" in stats
        assert "loaded_modules" in stats
        assert "loaded_module_count" in stats
        assert "total_module_count" in stats
        assert "feasible_modes" in stats
        assert "uptime_seconds" in stats
        assert "cpu_trend" in stats
        assert "ram_trend" in stats
        
        assert stats["initialized"] is True
        assert stats["loaded_module_count"] > 0
        assert stats["total_module_count"] == len(MODULE_PRIORITIES)
        
        await runtime.shutdown()
    
    @pytest.mark.asyncio
    async def test_uptime_tracking(self, runtime):
        """Uptime should be tracked."""
        await runtime.initialize()
        await asyncio.sleep(0.1)
        
        stats = runtime.get_stats()
        assert stats["uptime_seconds"] >= 0.1
        
        await runtime.shutdown()


# ── Shutdown Tests ──────────────────────────────────────────

class TestShutdown:
    """Test graceful shutdown."""
    
    @pytest.mark.asyncio
    async def test_shutdown_stops_monitoring(self, runtime):
        """Shutdown should stop monitoring."""
        await runtime.initialize()
        assert runtime.is_monitoring
        
        await runtime.shutdown()
        assert not runtime.is_monitoring
        assert not runtime.is_initialized
    
    @pytest.mark.asyncio
    async def test_shutdown_publishes_event(self, event_bus, runtime):
        """Shutdown should publish system.runtime.shutdown event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("system.runtime.shutdown", handler)
        await runtime.initialize()
        await runtime.shutdown()
        
        shutdown_events = [e for e in events if e.event_type == "system.runtime.shutdown"]
        assert len(shutdown_events) == 1
        assert "uptime_seconds" in shutdown_events[0].payload


# ── Integration Tests ───────────────────────────────────────

class TestIntegration:
    """Integration tests combining multiple features."""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, runtime):
        """Test complete lifecycle: init → use → switch → shutdown."""
        # Initialize
        await runtime.initialize(preferred_mode="cpu_only")
        assert runtime.current_mode == "cpu_only"
        assert runtime.is_initialized
        
        # Use resource queries
        usage = runtime.get_resource_usage()
        assert usage["cpu"]["cores"] > 0
        
        # Switch mode
        result = await runtime.switch_mode("low_memory")
        assert result is True
        assert runtime.current_mode == "low_memory"
        
        # Check stats
        stats = runtime.get_stats()
        assert stats["mode_switches"] == 1
        
        # Shutdown
        await runtime.shutdown()
        assert not runtime.is_initialized
    
    @pytest.mark.asyncio
    async def test_mode_switch_adjusts_modules(self, runtime):
        """Switching modes should adjust loaded modules."""
        await runtime.initialize(preferred_mode="full")
        assert runtime.is_module_loaded("local_llm")
        
        await runtime.switch_mode("low_memory")
        assert not runtime.is_module_loaded("local_llm")
        assert runtime.is_module_loaded("event_bus")  # Critical stays
        
        await runtime.shutdown()
