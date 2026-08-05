"""
ORION Adaptive Runtime
======================

The Adaptive Runtime is ORION's self-optimization engine. It detects
hardware capabilities, negotiates the best operating mode, monitors
resources, and dynamically adjusts module behavior.

Operating Modes:
- full:         All features enabled, local LLM + vision + cloud
- cpu_only:     No GPU, use cloud APIs for heavy tasks
- low_memory:   RAM constrained, unload heavy modules
- offline:      No internet, use only local resources
- server:       Headless mode, no GUI, optimized for throughput
- safe:         Minimal mode for diagnostics/recovery

Features:
- Hardware detection (CPU, RAM, disk, GPU, internet)
- Automatic operating mode negotiation
- Continuous resource monitoring with thresholds
- Event publishing via EventBus
- Module priority management
- Resource budgeting and throttling alerts

Usage:
    runtime = AdaptiveRuntime(event_bus)
    await runtime.initialize()
    profile = runtime.hardware_profile
    mode = runtime.current_mode
"""

import asyncio
import logging
import platform
import shutil
import socket
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import psutil

from orion.contracts.agent_contracts import Event
from orion.contracts.runtime_contracts import HardwareProfile, OperatingMode
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class ResourceThreshold(str, Enum):
    """Resource usage thresholds for alerts."""
    LOW = "low"           # < 50% usage
    MODERATE = "moderate" # 50-75% usage
    HIGH = "high"         # 75-90% usage
    CRITICAL = "critical" # > 90% usage


class ModulePriority(str, Enum):
    """Module priority levels for resource budgeting."""
    CRITICAL = "critical"    # EventBus, StateMachine — never unload
    HIGH = "high"            # Memory, TaskQueue — keep if possible
    MEDIUM = "medium"        # Vision, Browser — unload in low_memory
    LOW = "low"              # Local LLM, heavy analysis — cloud fallback


# Module registry: module_name -> priority
MODULE_PRIORITIES: Dict[str, ModulePriority] = {
    "event_bus": ModulePriority.CRITICAL,
    "state_machine": ModulePriority.CRITICAL,
    "task_queue": ModulePriority.HIGH,
    "memory": ModulePriority.HIGH,
    "agent_registry": ModulePriority.HIGH,
    "telegram_bot": ModulePriority.MEDIUM,
    "vision_engine": ModulePriority.MEDIUM,
    "browser": ModulePriority.MEDIUM,
    "local_llm": ModulePriority.LOW,
    "knowledge_graph": ModulePriority.LOW,
}

# Operating mode requirements
MODE_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "full":         {"min_ram_gb": 8.0,  "min_cpu_cores": 4, "requires_gpu": False, "requires_internet": False},
    "cpu_only":     {"min_ram_gb": 4.0,  "min_cpu_cores": 2, "requires_gpu": False, "requires_internet": False},
    "low_memory":   {"min_ram_gb": 0.0,  "min_cpu_cores": 1, "requires_gpu": False, "requires_internet": False},
    "offline":      {"min_ram_gb": 2.0,  "min_cpu_cores": 2, "requires_gpu": False, "requires_internet": False},
    "server":       {"min_ram_gb": 4.0,  "min_cpu_cores": 2, "requires_gpu": False, "requires_internet": True},
    "safe":         {"min_ram_gb": 0.0,  "min_cpu_cores": 1, "requires_gpu": False, "requires_internet": False},
}


class AdaptiveRuntime:
    """
    ORION's Adaptive Runtime engine.
    
    Detects hardware, negotiates operating mode, monitors resources,
    and publishes system events via EventBus.
    """
    
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._hardware_profile: Optional[HardwareProfile] = None
        self._current_mode: OperatingMode = "safe"
        self._target_mode: Optional[OperatingMode] = None
        self._initialized: bool = False
        self._monitoring: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # Resource history for trend analysis
        self._cpu_history: List[float] = []
        self._ram_history: List[float] = []
        self._max_history: int = 60  # Keep last 60 readings
        
        # Module load states
        self._loaded_modules: Set[str] = set()
        
        # Statistics
        self._mode_switches: int = 0
        self._resource_alerts: int = 0
        self._start_time: float = 0.0
        
        logger.info("AdaptiveRuntime created")
    
    # ── Properties ──────────────────────────────────────────────
    
    @property
    def hardware_profile(self) -> Optional[HardwareProfile]:
        """Get the detected hardware profile."""
        return self._hardware_profile
    
    @property
    def current_mode(self) -> OperatingMode:
        """Get the current operating mode."""
        return self._current_mode
    
    @property
    def is_initialized(self) -> bool:
        """Whether the runtime has been initialized."""
        return self._initialized
    
    @property
    def is_monitoring(self) -> bool:
        """Whether resource monitoring is active."""
        return self._monitoring
    
    @property
    def loaded_modules(self) -> Set[str]:
        """Get the set of currently loaded modules."""
        return self._loaded_modules.copy()
    
    # ── Initialization ──────────────────────────────────────────
    
    async def initialize(self, preferred_mode: Optional[OperatingMode] = None) -> None:
        """
        Initialize the Adaptive Runtime.
        
        Performs hardware detection, negotiates operating mode,
        and starts resource monitoring.
        
        Args:
            preferred_mode: If set, try to use this mode instead of auto-negotiating.
        """
        self._start_time = time.time()
        
        # Step 1: Detect hardware
        logger.info("Detecting hardware...")
        self._hardware_profile = await self._detect_hardware()
        
        # Step 2: Negotiate operating mode
        if preferred_mode:
            self._current_mode = preferred_mode
            self._target_mode = preferred_mode
            logger.info("Using preferred operating mode: %s", preferred_mode)
        else:
            self._current_mode = self._negotiate_mode(self._hardware_profile)
            logger.info("Auto-negotiated operating mode: %s", self._current_mode)
        
        # Step 3: Initialize modules based on mode
        await self._initialize_modules()
        
        # Step 4: Start resource monitoring
        await self.start_monitoring()
        
        self._initialized = True
        
        # Publish initialization event
        await self._event_bus.publish(Event(
            event_type="system.runtime.initialized",
            payload={
                "hardware_profile": self._hardware_profile.model_dump(),
                "operating_mode": self._current_mode,
                "loaded_modules": list(self._loaded_modules),
            },
            timestamp=time.time(),
            source="adaptive_runtime",
        ))
        
        logger.info("AdaptiveRuntime initialized successfully")
    
    async def shutdown(self) -> None:
        """Gracefully shut down the Adaptive Runtime."""
        await self.stop_monitoring()
        self._initialized = False
        
        await self._event_bus.publish(Event(
            event_type="system.runtime.shutdown",
            payload={"uptime_seconds": time.time() - self._start_time},
            timestamp=time.time(),
            source="adaptive_runtime",
        ))
        
        logger.info("AdaptiveRuntime shut down")
    
    # ── Hardware Detection ──────────────────────────────────────
    
    async def _detect_hardware(self) -> HardwareProfile:
        """
        Detect system hardware capabilities.
        
        Uses psutil for CPU/RAM/disk and socket for internet check.
        GPU detection is basic (checks for common GPU tools).
        """
        # CPU
        cpu_cores = psutil.cpu_count(logical=True) or 1
        
        # RAM
        mem = psutil.virtual_memory()
        total_ram_gb = round(mem.total / (1024 ** 3), 2)
        
        # Disk
        disk = psutil.disk_usage("/")
        # OS info
        os_name = platform.system()
        os_version = platform.release()
        
        # GPU detection (basic)
        has_gpu = False
        gpu_model = None
        try:
            # Check for NVIDIA GPU
            nvidia_smi = shutil.which("nvidia-smi")
            if nvidia_smi:
                has_gpu = True
                gpu_model = "NVIDIA (detected via nvidia-smi)"
        except Exception:
            pass
        
        # Internet connectivity
        internet_connected = await self._check_internet()
        
        profile = HardwareProfile(
            cpu_cores=cpu_cores,
            total_ram_gb=total_ram_gb,
            has_gpu=has_gpu,
            gpu_model=gpu_model,
            internet_connected=internet_connected,
            os_name=os_name,
            os_version=os_version,
        )
        
        logger.info(
            "Hardware detected: CPU=%d cores, RAM=%.1f GB, GPU=%s, Internet=%s, OS=%s %s",
            cpu_cores, total_ram_gb, has_gpu, internet_connected, os_name, os_version
        )
        
        # Publish hardware profile event
        await self._event_bus.publish(Event(
            event_type="system.hardware_profile",
            payload=profile.model_dump(),
            timestamp=time.time(),
            source="adaptive_runtime",
        ))
        
        return profile
    
    async def _check_internet(self, timeout: float = 3.0) -> bool:
        """Check internet connectivity by attempting DNS resolution."""
        try:
            # Try to connect to a well-known DNS server
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("8.8.8.8", 53),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, OSError, ConnectionRefusedError):
            return False
    
    # ── Operating Mode Negotiation ──────────────────────────────
    
    def _negotiate_mode(self, profile: HardwareProfile) -> OperatingMode:
        """
        Negotiate the best operating mode based on hardware profile.
        
        Logic:
        1. If no internet → offline
        2. If RAM < 4GB → low_memory
        3. If no GPU and RAM >= 4GB → cpu_only
        4. If GPU and RAM >= 8GB → full
        5. Default → cpu_only
        """
        if not profile.internet_connected:
            return "offline"
        
        if profile.total_ram_gb < 4.0:
            return "low_memory"
        
        if profile.has_gpu and profile.total_ram_gb >= 8.0:
            return "full"
        
        if not profile.has_gpu and profile.total_ram_gb >= 4.0:
            return "cpu_only"
        
        # Default fallback
        return "cpu_only"
    
    async def switch_mode(self, new_mode: OperatingMode, reason: str = "") -> bool:
        """
        Switch to a new operating mode.
        
        Args:
            new_mode: The target operating mode.
            reason: Reason for the switch.
            
        Returns:
            True if switch was successful.
        """
        async with self._lock:
            old_mode = self._current_mode
            
            if old_mode == new_mode:
                logger.info("Already in mode '%s', no switch needed", new_mode)
                return True
            
            # Check if mode is feasible with current hardware
            if self._hardware_profile and not self._is_mode_feasible(new_mode):
                logger.warning(
                    "Mode '%s' not feasible with current hardware (RAM=%.1f GB, cores=%d)",
                    new_mode, self._hardware_profile.total_ram_gb, self._hardware_profile.cpu_cores
                )
                return False
            
            # Perform the switch
            self._current_mode = new_mode
            self._target_mode = new_mode
            self._mode_switches += 1
            
            # Adjust modules for new mode
            await self._adjust_modules_for_mode(new_mode)
            
            # Publish mode change event
            await self._event_bus.publish(Event(
                event_type="system.operating_mode.changed",
                payload={
                    "old_mode": old_mode,
                    "new_mode": new_mode,
                    "reason": reason,
                    "timestamp": time.time(),
                },
                timestamp=time.time(),
                source="adaptive_runtime",
            ))
            
            logger.info("Operating mode switched: %s → %s (reason: %s)", old_mode, new_mode, reason)
            return True
    
    def _is_mode_feasible(self, mode: OperatingMode) -> bool:
        """Check if a mode is feasible with current hardware."""
        if not self._hardware_profile:
            return True  # Can't check, assume feasible
        
        thresholds = MODE_THRESHOLDS.get(mode, {})
        profile = self._hardware_profile
        
        if profile.total_ram_gb < thresholds.get("min_ram_gb", 0):
            return False
        if profile.cpu_cores < thresholds.get("min_cpu_cores", 0):
            return False
        if thresholds.get("requires_gpu", False) and not profile.has_gpu:
            return False
        if thresholds.get("requires_internet", False) and not profile.internet_connected:
            return False
        
        return True
    
    def get_feasible_modes(self) -> List[OperatingMode]:
        """Get list of operating modes feasible with current hardware."""
        modes: List[OperatingMode] = ["full", "cpu_only", "low_memory", "offline", "server", "safe"]
        return [m for m in modes if self._is_mode_feasible(m)]
    
    # ── Module Management ───────────────────────────────────────
    
    async def _initialize_modules(self) -> None:
        """Initialize modules based on current operating mode."""
        # Always load critical modules
        for module_name, priority in MODULE_PRIORITIES.items():
            if priority == ModulePriority.CRITICAL:
                self._loaded_modules.add(module_name)
        
        # Load based on mode
        await self._adjust_modules_for_mode(self._current_mode)
        
        logger.info("Initialized modules: %s", sorted(self._loaded_modules))
    
    async def _adjust_modules_for_mode(self, mode: OperatingMode) -> None:
        """Adjust loaded modules based on operating mode."""
        if mode == "full":
            # Load everything
            self._loaded_modules = set(MODULE_PRIORITIES.keys())
        
        elif mode == "cpu_only":
            # Skip local LLM, keep everything else
            self._loaded_modules = {
                name for name, prio in MODULE_PRIORITIES.items()
                if name != "local_llm"
            }
        
        elif mode == "low_memory":
            # Only critical + high priority
            self._loaded_modules = {
                name for name, prio in MODULE_PRIORITIES.items()
                if prio in (ModulePriority.CRITICAL, ModulePriority.HIGH)
            }
        
        elif mode == "offline":
            # No browser, no cloud-dependent modules
            self._loaded_modules = {
                name for name, prio in MODULE_PRIORITIES.items()
                if name not in ("browser",)
            }
        
        elif mode == "server":
            # No vision, no browser, no local LLM
            self._loaded_modules = {
                name for name, prio in MODULE_PRIORITIES.items()
                if name not in ("vision_engine", "browser", "local_llm")
            }
        
        elif mode == "safe":
            # Only critical modules
            self._loaded_modules = {
                name for name, prio in MODULE_PRIORITIES.items()
                if prio == ModulePriority.CRITICAL
            }
        
        await self._event_bus.publish(Event(
            event_type="system.modules.adjusted",
            payload={
                "mode": mode,
                "loaded_modules": sorted(self._loaded_modules),
            },
            timestamp=time.time(),
            source="adaptive_runtime",
        ))
    
    def is_module_loaded(self, module_name: str) -> bool:
        """Check if a module is currently loaded."""
        return module_name in self._loaded_modules
    
    def get_module_priority(self, module_name: str) -> Optional[ModulePriority]:
        """Get the priority of a module."""
        return MODULE_PRIORITIES.get(module_name)
    
    # ── Resource Monitoring ─────────────────────────────────────
    
    async def start_monitoring(self, interval_seconds: float = 5.0) -> None:
        """Start continuous resource monitoring."""
        if self._monitoring:
            logger.warning("Monitoring already active")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info("Resource monitoring started (interval=%.1fs)", interval_seconds)
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self, interval: float) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self._check_resources()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitoring error: %s", e)
                await asyncio.sleep(interval)
    
    async def _check_resources(self) -> None:
        """Check current resource usage and trigger alerts if needed."""
        cpu_percent = psutil.cpu_percent(interval=0)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        # Update history
        self._cpu_history.append(cpu_percent)
        self._ram_history.append(ram.percent)
        if len(self._cpu_history) > self._max_history:
            self._cpu_history.pop(0)
        if len(self._ram_history) > self._max_history:
            self._ram_history.pop(0)
        
        # Check thresholds
        cpu_threshold = self._get_threshold(cpu_percent)
        ram_threshold = self._get_threshold(ram.percent)
        disk_threshold = self._get_threshold(disk.percent)
        
        # Auto-switch to low_memory if RAM is critical
        if ram_threshold == ResourceThreshold.CRITICAL and self._current_mode != "low_memory":
            self._resource_alerts += 1
            await self._event_bus.publish(Event(
                event_type="system.resource.critical",
                payload={
                    "resource": "ram",
                    "percent": ram.percent,
                    "available_gb": round(ram.available / (1024 ** 3), 2),
                    "current_mode": self._current_mode,
                },
                timestamp=time.time(),
                source="adaptive_runtime",
            ))
            
            # Auto-switch to low_memory mode
            await self.switch_mode("low_memory", reason="RAM critical")
        
        # Publish periodic resource status
        if cpu_threshold in (ResourceThreshold.HIGH, ResourceThreshold.CRITICAL) or \
           ram_threshold in (ResourceThreshold.HIGH, ResourceThreshold.CRITICAL):
            self._resource_alerts += 1
            await self._event_bus.publish(Event(
                event_type="system.resource.alert",
                payload={
                    "cpu_percent": cpu_percent,
                    "cpu_threshold": cpu_threshold.value,
                    "ram_percent": ram.percent,
                    "ram_threshold": ram_threshold.value,
                    "disk_percent": disk.percent,
                    "disk_threshold": disk_threshold.value,
                },
                timestamp=time.time(),
                source="adaptive_runtime",
            ))
    
    @staticmethod
    def _get_threshold(percent: float) -> ResourceThreshold:
        """Get the threshold level for a usage percentage."""
        if percent >= 90:
            return ResourceThreshold.CRITICAL
        elif percent >= 75:
            return ResourceThreshold.HIGH
        elif percent >= 50:
            return ResourceThreshold.MODERATE
        return ResourceThreshold.LOW
    
    # ── Resource Queries ────────────────────────────────────────
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage snapshot."""
        cpu_percent = psutil.cpu_percent(interval=0)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(logical=True),
                "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "threshold": self._get_threshold(cpu_percent).value,
            },
            "ram": {
                "total_gb": round(ram.total / (1024 ** 3), 2),
                "available_gb": round(ram.available / (1024 ** 3), 2),
                "used_gb": round(ram.used / (1024 ** 3), 2),
                "percent": ram.percent,
                "threshold": self._get_threshold(ram.percent).value,
            },
            "disk": {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "free_gb": round(disk.free / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "percent": disk.percent,
                "threshold": self._get_threshold(disk.percent).value,
            },
        }
    
    def get_cpu_trend(self) -> Dict[str, Any]:
        """Get CPU usage trend from history."""
        if not self._cpu_history:
            return {"samples": 0, "avg": 0, "min": 0, "max": 0, "current": 0}
        
        return {
            "samples": len(self._cpu_history),
            "avg": round(sum(self._cpu_history) / len(self._cpu_history), 1),
            "min": round(min(self._cpu_history), 1),
            "max": round(max(self._cpu_history), 1),
            "current": round(self._cpu_history[-1], 1),
        }
    
    def get_ram_trend(self) -> Dict[str, Any]:
        """Get RAM usage trend from history."""
        if not self._ram_history:
            return {"samples": 0, "avg": 0, "min": 0, "max": 0, "current": 0}
        
        return {
            "samples": len(self._ram_history),
            "avg": round(sum(self._ram_history) / len(self._ram_history), 1),
            "min": round(min(self._ram_history), 1),
            "max": round(max(self._ram_history), 1),
            "current": round(self._ram_history[-1], 1),
        }
    
    # ── Statistics ──────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Adaptive Runtime statistics."""
        uptime = time.time() - self._start_time if self._start_time else 0
        
        return {
            "initialized": self._initialized,
            "monitoring": self._monitoring,
            "current_mode": self._current_mode,
            "target_mode": self._target_mode,
            "mode_switches": self._mode_switches,
            "resource_alerts": self._resource_alerts,
            "loaded_modules": sorted(self._loaded_modules),
            "loaded_module_count": len(self._loaded_modules),
            "total_module_count": len(MODULE_PRIORITIES),
            "feasible_modes": self.get_feasible_modes(),
            "uptime_seconds": round(uptime, 1),
            "cpu_trend": self.get_cpu_trend(),
            "ram_trend": self.get_ram_trend(),
        }
