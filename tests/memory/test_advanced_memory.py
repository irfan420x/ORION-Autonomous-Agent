"""
Tests for ORION Advanced Memory System
=======================================
"""

import asyncio
import pytest
import time

from orion.core.communication.event_bus import EventBus
from orion.memory.advanced_memory import (
    AdvancedMemorySystem, MemoryEntry, MemoryGraph,
    MemoryTier, MemoryImportance,
)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
async def memory_system(event_bus, tmp_path):
    db_path = str(tmp_path / "test_memory.db")
    system = AdvancedMemorySystem(event_bus, db_path=db_path)
    await system.start()
    yield system
    await system.stop()


@pytest.fixture
def graph():
    return MemoryGraph()


# ── MemoryEntry Tests ────────────────────────────────────────

class TestMemoryEntry:
    def test_creation(self):
        entry = MemoryEntry("key1", "value1")
        assert entry.key == "key1"
        assert entry.value == "value1"
        assert entry.tier == MemoryTier.SESSION

    def test_touch(self):
        entry = MemoryEntry("key1", "value1")
        old_access = entry.accessed_at
        time.sleep(0.01)
        entry.touch()
        assert entry.access_count == 1
        assert entry.accessed_at > old_access

    def test_expired(self):
        entry = MemoryEntry("key1", "value1", ttl_seconds=0)
        time.sleep(0.01)
        assert entry.is_expired()

    def test_not_expired(self):
        entry = MemoryEntry("key1", "value1", ttl_seconds=3600)
        assert not entry.is_expired()

    def test_to_dict(self):
        entry = MemoryEntry("key1", "value1", tags=["test"])
        d = entry.to_dict()
        assert d["key"] == "key1"
        assert "test" in d["tags"]


# ── MemoryGraph Tests ────────────────────────────────────────

class TestMemoryGraph:
    def test_add_and_get(self, graph):
        entry = MemoryEntry("key1", "value1")
        graph.add(entry)
        assert graph.get(entry.id) == entry

    def test_get_by_key(self, graph):
        entry = MemoryEntry("key1", "value1")
        graph.add(entry)
        assert graph.get_by_key("key1") == entry

    def test_get_related(self, graph):
        entry1 = MemoryEntry("key1", "value1")
        entry2 = MemoryEntry("key2", "value2", associations=["key1"])
        graph.add(entry1)
        graph.add(entry2)
        
        related = graph.get_related(entry1.id)
        assert len(related) == 1
        assert related[0].key == "key2"

    def test_get_by_tag(self, graph):
        entry = MemoryEntry("key1", "value1", tags=["important"])
        graph.add(entry)
        
        results = graph.get_by_tag("important")
        assert len(results) == 1

    def test_search(self, graph):
        entry1 = MemoryEntry("user_name", "Alice")
        entry2 = MemoryEntry("user_age", "30")
        graph.add(entry1)
        graph.add(entry2)
        
        results = graph.search("Alice")
        assert len(results) == 1
        assert results[0].key == "user_name"

    def test_remove(self, graph):
        entry = MemoryEntry("key1", "value1")
        graph.add(entry)
        assert graph.remove(entry.id) is True
        assert graph.get(entry.id) is None

    def test_stats(self, graph):
        entry = MemoryEntry("key1", "value1", tags=["test"])
        graph.add(entry)
        
        stats = graph.get_stats()
        assert stats["total_memories"] == 1
        assert stats["total_tags"] == 1


# ── AdvancedMemorySystem Tests ───────────────────────────────

class TestAdvancedMemorySystem:
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, memory_system):
        await memory_system.store("key1", "value1")
        entry = await memory_system.retrieve("key1")
        assert entry is not None
        assert entry.value == "value1"

    @pytest.mark.asyncio
    async def test_store_with_tags(self, memory_system):
        await memory_system.store("key1", "value1", tags=["important"])
        results = await memory_system.search("", tags=["important"])
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search(self, memory_system):
        await memory_system.store("user_name", "Alice")
        await memory_system.store("user_age", "30")
        
        results = await memory_system.search("Alice")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_forget(self, memory_system):
        await memory_system.store("key1", "value1")
        assert await memory_system.forget("key1") is True
        assert await memory_system.retrieve("key1") is None

    @pytest.mark.asyncio
    async def test_reflect(self, memory_system):
        await memory_system.store("topic_a", "info about A", tags=["topic"])
        await memory_system.store("topic_b", "more about A", tags=["topic"])
        
        result = await memory_system.reflect("A")
        assert result["memory_count"] >= 1

    @pytest.mark.asyncio
    async def test_working_memory(self, memory_system):
        await memory_system.store("key1", "value1", tier=MemoryTier.WORKING)
        entry = await memory_system.retrieve("key1")
        assert entry is not None
        assert entry.tier == MemoryTier.WORKING

    @pytest.mark.asyncio
    async def test_stats(self, memory_system):
        await memory_system.store("key1", "value1")
        stats = memory_system.get_stats()
        assert stats["total_stores"] == 1

    @pytest.mark.asyncio
    async def test_persistence(self, event_bus, tmp_path):
        """Test that memories persist across restarts."""
        db_path = str(tmp_path / "test_persist.db")
        
        # First session
        system1 = AdvancedMemorySystem(event_bus, db_path=db_path)
        await system1.start()
        await system1.store("key1", "value1", tier=MemoryTier.LONG_TERM)
        await system1.stop()
        
        # Second session
        system2 = AdvancedMemorySystem(event_bus, db_path=db_path)
        await system2.start()
        entry = await system2.retrieve("key1")
        assert entry is not None
        assert entry.value == "value1"
        await system2.stop()
