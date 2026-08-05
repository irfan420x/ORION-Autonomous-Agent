"""
ORION Dependency Engine
=======================

Detects, installs, updates, and repairs system/Python dependencies.
Uses PlatformMapper for cross-platform package names.

Features:
- Check if a dependency is installed (binary or Python package)
- Auto-install missing dependencies via pip or apt/brew/choco
- Version checking
- Event publishing via EventBus

Usage:
    engine = DependencyEngine(event_bus)
    result = await engine.check_dependency("psutil")
    if not result.is_ok:
        await engine.install_dependency("psutil")
"""

import asyncio
import importlib
import logging
import shutil
import time
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.contracts.dependency_contracts import (
    DependencyCheckResult,
    DependencyInfo,
    DependencyStatus,
)
from orion.core.communication.event_bus import EventBus
from orion.dependency.platform_mapper import PlatformMapper

logger = logging.getLogger(__name__)


class DependencyEngine:
    """
    Manages dependency detection, installation, and repair.
    """
    
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._platform = PlatformMapper()
        
        # Cache of checked dependencies
        self._cache: Dict[str, DependencyCheckResult] = {}
        
        # Stats
        self._total_checks: int = 0
        self._total_installs: int = 0
        self._total_failures: int = 0
        
        logger.info("DependencyEngine initialized")
    
    async def check_dependency(self, name: str) -> DependencyCheckResult:
        """
        Check if a dependency is installed.
        
        Checks in order:
        1. Is it a Python package? (importlib)
        2. Is it a binary? (shutil.which)
        """
        self._total_checks += 1
        now = time.time()
        
        # Check if it's a Python package
        pip_name = self._platform.get_pip_name(name)
        if pip_name:
            try:
                mod = importlib.import_module(pip_name)
                version = getattr(mod, "__version__", None)
                info = DependencyInfo(
                    name=name,
                    version=version,
                    status="INSTALLED",
                    platform_specific_name=pip_name,
                )
                result = DependencyCheckResult(
                    dependency=info,
                    is_ok=True,
                    message=f"Python package '{pip_name}' is installed" + (f" (v{version})" if version else ""),
                )
            except ImportError:
                info = DependencyInfo(
                    name=name,
                    status="MISSING",
                    platform_specific_name=pip_name,
                    install_command=f"pip install {pip_name}",
                )
                result = DependencyCheckResult(
                    dependency=info,
                    is_ok=False,
                    message=f"Python package '{pip_name}' is not installed",
                )
        else:
            # Check if it's a binary
            binary = shutil.which(name)
            if binary:
                info = DependencyInfo(
                    name=name,
                    status="INSTALLED",
                )
                result = DependencyCheckResult(
                    dependency=info,
                    is_ok=True,
                    message=f"Binary '{name}' found at {binary}",
                )
            else:
                install_cmd = self._platform.get_install_command(name)
                info = DependencyInfo(
                    name=name,
                    status="MISSING",
                    install_command=install_cmd,
                )
                result = DependencyCheckResult(
                    dependency=info,
                    is_ok=False,
                    message=f"Dependency '{name}' not found" + (f". Install: {install_cmd}" if install_cmd else ""),
                )
        
        # Cache result
        self._cache[name] = result
        
        # Publish event
        await self._event_bus.publish(Event(
            event_type="system.dependency.checked",
            payload={
                "name": name,
                "status": info.status,
                "is_ok": result.is_ok,
            },
            timestamp=now,
            source="dependency_engine",
        ))
        
        return result
    
    async def install_dependency(self, name: str) -> bool:
        """
        Install a missing dependency.
        
        Returns True if installation succeeded.
        """
        self._total_installs += 1
        
        pip_name = self._platform.get_pip_name(name)
        
        if pip_name:
            return await self._install_pip(pip_name, name)
        
        # Try system package manager
        install_cmd = self._platform.get_install_command(name)
        if install_cmd:
            return await self._run_install_command(install_cmd, name)
        
        logger.warning("No install method known for '%s'", name)
        self._total_failures += 1
        return False
    
    async def _install_pip(self, pip_name: str, display_name: str) -> bool:
        """Install a Python package via pip."""
        logger.info("Installing pip package: %s", pip_name)
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "pip", "install", pip_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            
            if proc.returncode == 0:
                logger.info("Successfully installed %s", pip_name)
                
                await self._event_bus.publish(Event(
                    event_type="system.dependency.installed",
                    payload={"name": display_name, "method": "pip", "success": True},
                    timestamp=time.time(),
                    source="dependency_engine",
                ))
                
                # Clear cache
                self._cache.pop(display_name, None)
                return True
            else:
                error = stderr.decode().strip()
                logger.error("Failed to install %s: %s", pip_name, error)
                self._total_failures += 1
                return False
        
        except asyncio.TimeoutError:
            logger.error("Timeout installing %s", pip_name)
            self._total_failures += 1
            return False
        except Exception as e:
            logger.error("Error installing %s: %s", pip_name, e)
            self._total_failures += 1
            return False
    
    async def _run_install_command(self, command: str, display_name: str) -> bool:
        """Run a system install command."""
        logger.info("Running install command: %s", command)
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            
            if proc.returncode == 0:
                logger.info("Successfully installed %s", display_name)
                
                await self._event_bus.publish(Event(
                    event_type="system.dependency.installed",
                    payload={"name": display_name, "method": "system", "success": True},
                    timestamp=time.time(),
                    source="dependency_engine",
                ))
                
                self._cache.pop(display_name, None)
                return True
            else:
                error = stderr.decode().strip()
                logger.error("Failed to install %s: %s", display_name, error)
                self._total_failures += 1
                return False
        
        except asyncio.TimeoutError:
            logger.error("Timeout installing %s", display_name)
            self._total_failures += 1
            return False
        except Exception as e:
            logger.error("Error installing %s: %s", display_name, e)
            self._total_failures += 1
            return False
    
    async def check_multiple(self, names: List[str]) -> Dict[str, DependencyCheckResult]:
        """Check multiple dependencies at once."""
        results = {}
        for name in names:
            results[name] = await self.check_dependency(name)
        return results
    
    async def ensure_dependencies(self, names: List[str]) -> Dict[str, bool]:
        """
        Ensure all listed dependencies are installed.
        Installs any that are missing.
        """
        results = {}
        for name in names:
            check = await self.check_dependency(name)
            if check.is_ok:
                results[name] = True
            else:
                results[name] = await self.install_dependency(name)
        return results
    
    def get_cached(self, name: str) -> Optional[DependencyCheckResult]:
        """Get a cached check result."""
        return self._cache.get(name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dependency engine statistics."""
        return {
            "total_checks": self._total_checks,
            "total_installs": self._total_installs,
            "total_failures": self._total_failures,
            "cached_results": len(self._cache),
            "known_dependencies": len(self._platform.get_all_mappings()),
            "platform": self._platform._os,
        }
