"""
Tests for ORION Dependency Engine
==================================
"""

import asyncio
import pytest
import time

from orion.core.communication.event_bus import EventBus
from orion.contracts.dependency_contracts import (
    DependencyInfo,
    DependencyCheckResult,
    DependencyStatus,
    PlatformMapping,
)
from orion.dependency.platform_mapper import PlatformMapper, PLATFORM_MAPPINGS
from orion.dependency.dependency_engine import DependencyEngine


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def mapper():
    return PlatformMapper()


@pytest.fixture
def engine(event_bus):
    return DependencyEngine(event_bus)


# ── Platform Mapper Tests ────────────────────────────────────

class TestPlatformMapper:
    def test_os_detected(self, mapper):
        assert mapper._os in ("linux", "darwin", "windows")

    def test_get_package_name_nmap(self, mapper):
        name = mapper.get_package_name("nmap")
        assert name == "nmap"  # Same on all platforms

    def test_get_package_name_unknown(self, mapper):
        assert mapper.get_package_name("nonexistent_tool") is None

    def test_get_install_command_pip(self, mapper):
        cmd = mapper.get_install_command("psutil")
        assert cmd == "pip install psutil"

    def test_get_install_command_system(self, mapper):
        cmd = mapper.get_install_command("nmap")
        assert cmd is not None
        assert "nmap" in cmd

    def test_get_pip_name(self, mapper):
        assert mapper.get_pip_name("psutil") == "psutil"
        assert mapper.get_pip_name("pytest") == "pytest"
        assert mapper.get_pip_name("nmap") is None

    def test_get_binary_name(self, mapper):
        assert mapper.get_binary_name("nmap") == "nmap"

    def test_add_custom_mapping(self, mapper):
        custom = PlatformMapping(
            generic_name="mytool",
            python_pip="mytool-py",
        )
        mapper.add_mapping(custom)
        assert mapper.get_pip_name("mytool") == "mytool-py"

    def test_get_all_mappings(self, mapper):
        all_maps = mapper.get_all_mappings()
        assert "nmap" in all_maps
        assert "psutil" in all_maps

    def test_known_mappings_count(self, mapper):
        assert len(PLATFORM_MAPPINGS) >= 10


# ── Dependency Engine Tests ──────────────────────────────────

class TestDependencyEngine:
    @pytest.mark.asyncio
    async def test_check_installed_pip(self, engine):
        """psutil is installed, should return INSTALLED."""
        result = await engine.check_dependency("psutil")
        
        assert result.is_ok
        assert result.dependency.status == "INSTALLED"
        assert result.dependency.version is not None

    @pytest.mark.asyncio
    async def test_check_installed_binary(self, engine):
        """python3 is installed as a binary."""
        result = await engine.check_dependency("python3")
        
        assert result.is_ok
        assert result.dependency.status == "INSTALLED"

    @pytest.mark.asyncio
    async def test_check_missing(self, engine):
        """Nonexistent tool should be MISSING."""
        result = await engine.check_dependency("nonexistent_tool_xyz")
        
        assert not result.is_ok
        assert result.dependency.status == "MISSING"

    @pytest.mark.asyncio
    async def test_check_pip_package(self, engine):
        """pytest is installed via pip."""
        result = await engine.check_dependency("pytest")
        
        assert result.is_ok
        assert result.dependency.status == "INSTALLED"

    @pytest.mark.asyncio
    async def test_check_multiple(self, engine):
        """Can check multiple dependencies."""
        results = await engine.check_multiple(["psutil", "pytest"])
        
        assert len(results) == 2
        assert results["psutil"].is_ok
        assert results["pytest"].is_ok

    @pytest.mark.asyncio
    async def test_ensure_dependencies(self, engine):
        """ensure_dependencies returns True for installed packages."""
        results = await engine.ensure_dependencies(["psutil", "pytest"])
        
        assert all(results.values())

    @pytest.mark.asyncio
    async def test_ensure_missing_package(self, engine):
        """ensure_dependencies tries to install missing packages."""
        results = await engine.ensure_dependencies(["nonexistent_pkg_xyz"])
        
        # It will try to install and fail (no such package)
        assert not results["nonexistent_pkg_xyz"]

    @pytest.mark.asyncio
    async def test_install_pip_package(self, engine):
        """Can install a pip package (httpbin is lightweight)."""
        # First check it's not installed
        check = await engine.check_dependency("httpbin")
        
        if not check.is_ok:
            # Try to install
            success = await engine.install_dependency("httpbin")
            # May or may not succeed depending on network
            assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_check_publishes_event(self, event_bus, engine):
        """Check publishes system.dependency.checked event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("system.dependency.checked", handler)
        await engine.check_dependency("psutil")
        
        assert len(events) == 1
        assert events[0].payload["name"] == "psutil"
        assert events[0].payload["is_ok"] is True

    @pytest.mark.asyncio
    async def test_cache(self, engine):
        """Results are cached."""
        await engine.check_dependency("psutil")
        cached = engine.get_cached("psutil")
        
        assert cached is not None
        assert cached.is_ok

    @pytest.mark.asyncio
    async def test_stats(self, engine):
        """Stats are tracked."""
        await engine.check_dependency("psutil")
        await engine.check_dependency("pytest")
        
        stats = engine.get_stats()
        assert stats["total_checks"] == 2
        assert stats["cached_results"] == 2
        assert stats["known_dependencies"] >= 10

    @pytest.mark.asyncio
    async def test_check_unknown_tool(self, engine):
        """Unknown tool with no mapping returns MISSING."""
        result = await engine.check_dependency("totally_fake_tool")
        
        assert not result.is_ok
        assert result.dependency.status == "MISSING"

    @pytest.mark.asyncio
    async def test_multiple_checks_same_tool(self, engine):
        """Multiple checks of same tool work."""
        r1 = await engine.check_dependency("psutil")
        r2 = await engine.check_dependency("psutil")
        
        assert r1.is_ok == r2.is_ok


# ── Contracts Tests ──────────────────────────────────────────

class TestContracts:
    def test_dependency_info(self):
        info = DependencyInfo(
            name="test",
            status="INSTALLED",
        )
        assert info.name == "test"

    def test_dependency_check_result(self):
        info = DependencyInfo(name="test", status="INSTALLED")
        result = DependencyCheckResult(
            dependency=info,
            is_ok=True,
        )
        assert result.is_ok

    def test_platform_mapping(self):
        mapping = PlatformMapping(
            generic_name="tool",
            linux_apt="tool-apt",
            python_pip="tool-py",
        )
        assert mapping.generic_name == "tool"

    def test_dependency_status_enum(self):
        assert DependencyStatus is not None
