"""
Tests for ORION Rust Bridge (M2.4)
===================================
"""

import asyncio
import os
import pytest
import time

from orion.rust_bridge import RustBridge


@pytest.fixture
def bridge():
    return RustBridge()


class TestRustBridge:
    def test_binary_detection(self, bridge):
        """Detects if Rust binary is available."""
        # Binary may or may not be available depending on build
        assert isinstance(bridge.is_available, bool)

    @pytest.mark.asyncio
    async def test_health(self, bridge):
        """Health check returns valid data."""
        if not bridge.is_available:
            pytest.skip("Rust binary not available")
        
        result = await bridge.health()
        
        assert "status" in result
        assert result["status"] in ("HEALTHY", "DEGRADED", "CRITICAL")
        assert "cpu_cores" in result
        assert result["cpu_cores"] > 0

    @pytest.mark.asyncio
    async def test_snapshot(self, bridge):
        """Snapshot returns system data."""
        if not bridge.is_available:
            pytest.skip("Rust binary not available")
        
        result = await bridge.snapshot()
        
        assert "cpu_count" in result
        assert "total_memory_mb" in result
        assert "process_count" in result
        assert result["cpu_count"] > 0

    @pytest.mark.asyncio
    async def test_processes(self, bridge):
        """Processes returns list."""
        if not bridge.is_available:
            pytest.skip("Rust binary not available")
        
        result = await bridge.processes(5)
        
        assert isinstance(result, list)
        # May be empty if binary is not available

    @pytest.mark.asyncio
    async def test_unavailable_bridge(self):
        """Bridge with bad path reports unavailable."""
        bridge = RustBridge("/nonexistent/binary")
        
        assert not bridge.is_available
        
        result = await bridge.health()
        assert "error" in result

    @pytest.mark.asyncio
    async def test_health_performance(self, bridge):
        """Rust health check is fast (<2s)."""
        if not bridge.is_available:
            pytest.skip("Rust binary not available")
        
        start = time.time()
        await bridge.health()
        elapsed = time.time() - start
        
        assert elapsed < 2.0, f"Health check took {elapsed:.2f}s, expected <2s"
