"""
Unit Tests for ORION Memory System
===================================

Tests cover:
- SessionMemory: LRU eviction, TTL, tags, search
- LongTermMemory: SQLite persistence, FTS5 search
- EpisodicMemory: Episode logging, pattern recognition
- SemanticMemory: Vector search, similarity
- MemoryManager: Unified API, cross-tier search
"""

import asyncio
import json
import os
import pytest
import tempfile
import time

from orion.contracts.memory_contracts import MemoryType, MemoryConfig
from orion.core.communication.event_bus import EventBus
from orion.memory.session_memory import SessionMemory
from orion.memory.long_term_memory import LongTermMemory
from orion.memory.episodic_memory import EpisodicMemory
from orion.memory.semantic_memory import SemanticMemory
from orion.memory.memory_manager import MemoryManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def event_bus():
    return EventBus(max_history=100)


@pytest.fixture
def session_memory(event_bus):
    return SessionMemory(event_bus, max_size=100, ttl_seconds=3600)


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        yield f.name
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
async def long_term_memory(event_bus, temp_db_path):
    ltm = LongTermMemory(event_bus, db_path=temp_db_path)
    await ltm.start()
    yield ltm
    await ltm.stop()


@pytest.fixture
def episodic_memory(event_bus):
    return EpisodicMemory(event_bus, max_episodes=100)


@pytest.fixture
def semantic_memory(event_bus):
    return SemanticMemory(event_bus, dimension=64)


@pytest.fixture
async def memory_manager(event_bus, temp_db_path):
    config = MemoryConfig(
        long_term_db_path=temp_db_path,
        session_max_size=100,
    )
    manager = MemoryManager(event_bus, config)
    await manager.start()
    yield manager
    await manager.stop()


# ============================================================================
# Session Memory Tests
# ============================================================================

class TestSessionMemory:
    @pytest.mark.asyncio
    async def test_put_and_get(self, session_memory):
        await session_memory.put("key1", "value1")
        result = await session_memory.get("key1")
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, session_memory):
        result = await session_memory.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_lru_eviction(self, event_bus):
        sm = SessionMemory(event_bus, max_size=3)
        await sm.put("a", 1)
        await sm.put("b", 2)
        await sm.put("c", 3)
        await sm.put("d", 4)  # Should evict "a"
        
        assert await sm.get("a") is None
        assert await sm.get("b") == 2
    
    @pytest.mark.asyncio
    async def test_update_existing(self, session_memory):
        await session_memory.put("key1", "old")
        await session_memory.put("key1", "new")
        result = await session_memory.get("key1")
        assert result == "new"
    
    @pytest.mark.asyncio
    async def test_delete(self, session_memory):
        await session_memory.put("key1", "value1")
        deleted = await session_memory.delete("key1")
        assert deleted is True
        assert await session_memory.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_exists(self, session_memory):
        await session_memory.put("key1", "value1")
        assert await session_memory.exists("key1") is True
        assert await session_memory.exists("nonexistent") is False
    
    @pytest.mark.asyncio
    async def test_tags(self, session_memory):
        await session_memory.put("key1", "value1", tags=["important", "user"])
        await session_memory.put("key2", "value2", tags=["system"])
        
        results = await session_memory.get_by_tag("important")
        assert len(results) == 1
        assert results[0].key == "key1"
    
    @pytest.mark.asyncio
    async def test_search(self, session_memory):
        await session_memory.put("user_name", "Irfan")
        await session_memory.put("user_email", "irfan@example.com")
        await session_memory.put("system_status", "running")
        
        results = await session_memory.search("user")
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_stats(self, session_memory):
        await session_memory.put("key1", "value1")
        await session_memory.put("key2", "value2")
        
        stats = session_memory.get_stats()
        assert stats.total_entries == 2


# ============================================================================
# Long-term Memory Tests
# ============================================================================

class TestLongTermMemory:
    @pytest.mark.asyncio
    async def test_put_and_get(self, long_term_memory):
        await long_term_memory.put("key1", {"data": "value1"})
        result = await long_term_memory.get("key1")
        assert result == {"data": "value1"}
    
    @pytest.mark.asyncio
    async def test_fts_search(self, long_term_memory):
        await long_term_memory.put("doc1", "Python programming guide")
        await long_term_memory.put("doc2", "JavaScript web development")
        await long_term_memory.put("doc3", "Python machine learning")
        
        results = await long_term_memory.search("Python")
        assert len(results) >= 2
    
    @pytest.mark.asyncio
    async def test_delete(self, long_term_memory):
        await long_term_memory.put("key1", "value1")
        deleted = await long_term_memory.delete("key1")
        assert deleted is True
        assert await long_term_memory.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_persistence(self, event_bus, temp_db_path):
        # Write data
        ltm1 = LongTermMemory(event_bus, db_path=temp_db_path)
        await ltm1.start()
        await ltm1.put("persistent_key", "persistent_value")
        await ltm1.stop()
        
        # Read from new instance
        ltm2 = LongTermMemory(event_bus, db_path=temp_db_path)
        await ltm2.start()
        result = await ltm2.get("persistent_key")
        assert result == "persistent_value"
        await ltm2.stop()
    
    @pytest.mark.asyncio
    async def test_tags(self, long_term_memory):
        await long_term_memory.put("key1", "value1", tags=["important"])
        await long_term_memory.put("key2", "value2", tags=["system"])
        
        results = await long_term_memory.get_by_tag("important")
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_stats(self, long_term_memory):
        await long_term_memory.put("key1", "value1")
        stats = long_term_memory.get_stats()
        assert stats.total_entries == 1


# ============================================================================
# Episodic Memory Tests
# ============================================================================

class TestEpisodicMemory:
    @pytest.mark.asyncio
    async def test_log_episode(self, episodic_memory):
        episode = await episodic_memory.log_episode(
            action="Install package",
            context={"package": "numpy"},
            outcome="Successfully installed",
            success=True,
        )
        assert episode.success is True
        assert episode.action == "Install package"
    
    @pytest.mark.asyncio
    async def test_get_similar_episodes(self, episodic_memory):
        await episodic_memory.log_episode("Install numpy", {}, "ok", True)
        await episodic_memory.log_episode("Install pandas", {}, "ok", True)
        await episodic_memory.log_episode("Run tests", {}, "ok", True)
        
        similar = await episodic_memory.get_similar_episodes("Install scipy")
        assert len(similar) >= 1
    
    @pytest.mark.asyncio
    async def test_get_lessons(self, episodic_memory):
        await episodic_memory.log_episode(
            "Install package",
            {},
            "Failed",
            False,
            lessons_learned=["Check Python version first"],
        )
        
        lessons = await episodic_memory.get_lessons()
        assert "Check Python version first" in lessons
    
    @pytest.mark.asyncio
    async def test_success_rate(self, episodic_memory):
        await episodic_memory.log_episode("Action1", {}, "ok", True)
        await episodic_memory.log_episode("Action2", {}, "ok", True)
        await episodic_memory.log_episode("Action3", {}, "fail", False)
        
        rate = await episodic_memory.get_success_rate()
        assert abs(rate - 0.666) < 0.01
    
    @pytest.mark.asyncio
    async def test_stats(self, episodic_memory):
        await episodic_memory.log_episode("Test", {}, "ok", True)
        stats = episodic_memory.get_stats()
        assert stats["total_episodes"] == 1


# ============================================================================
# Semantic Memory Tests
# ============================================================================

class TestSemanticMemory:
    @pytest.mark.asyncio
    async def test_add_and_search(self, semantic_memory):
        await semantic_memory.add_document("doc1", "Python programming", {"lang": "python"})
        await semantic_memory.add_document("doc2", "JavaScript web dev", {"lang": "javascript"})
        
        results = await semantic_memory.search("Python coding")
        assert len(results) >= 1
        assert results[0]["doc_id"] == "doc1"
    
    @pytest.mark.asyncio
    async def test_batch_add(self, semantic_memory):
        docs = [
            {"doc_id": "d1", "content": "Machine learning"},
            {"doc_id": "d2", "content": "Deep learning"},
        ]
        count = await semantic_memory.add_documents_batch(docs)
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_delete(self, semantic_memory):
        await semantic_memory.add_document("doc1", "Test content")
        deleted = await semantic_memory.delete_document("doc1")
        assert deleted is True
    
    @pytest.mark.asyncio
    async def test_metadata_filter(self, semantic_memory):
        await semantic_memory.add_document("doc1", "Python", {"type": "tutorial"})
        await semantic_memory.add_document("doc2", "Python", {"type": "reference"})
        
        results = await semantic_memory.search("Python", metadata_filter={"type": "tutorial"})
        assert len(results) == 1
        assert results[0]["doc_id"] == "doc1"
    
    @pytest.mark.asyncio
    async def test_stats(self, semantic_memory):
        await semantic_memory.add_document("doc1", "Test")
        stats = semantic_memory.get_stats()
        assert stats["total_documents"] == 1


# ============================================================================
# Memory Manager Tests
# ============================================================================

class TestMemoryManager:
    @pytest.mark.asyncio
    async def test_remember_session(self, memory_manager):
        await memory_manager.remember("key1", "value1", MemoryType.SESSION)
        result = await memory_manager.recall("key1", MemoryType.SESSION)
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_remember_long_term(self, memory_manager):
        await memory_manager.remember("key1", {"data": "value"}, MemoryType.LONG_TERM)
        result = await memory_manager.recall("key1", MemoryType.LONG_TERM)
        assert result == {"data": "value"}
    
    @pytest.mark.asyncio
    async def test_remember_semantic(self, memory_manager):
        await memory_manager.remember("doc1", "Python programming", MemoryType.SEMANTIC)
        result = await memory_manager.recall("doc1", MemoryType.SEMANTIC)
        assert result == "Python programming"
    
    @pytest.mark.asyncio
    async def test_recall_all_tiers(self, memory_manager):
        await memory_manager.remember("key1", "session_val", MemoryType.SESSION)
        await memory_manager.remember("key2", "ltm_val", MemoryType.LONG_TERM)
        
        # Should find in session
        result1 = await memory_manager.recall_all_tiers("key1")
        assert result1 == "session_val"
        
        # Should find in long-term and promote to session
        result2 = await memory_manager.recall_all_tiers("key2")
        assert result2 == "ltm_val"
    
    @pytest.mark.asyncio
    async def test_forget(self, memory_manager):
        await memory_manager.remember("key1", "value1", MemoryType.SESSION)
        deleted = await memory_manager.forget("key1")
        assert deleted is True
    
    @pytest.mark.asyncio
    async def test_search_all(self, memory_manager):
        await memory_manager.remember("key1", "Python code", MemoryType.SESSION)
        await memory_manager.remember("key2", "Python tutorial", MemoryType.LONG_TERM)
        
        results = await memory_manager.search_all("Python")
        assert "session" in results
        assert "long_term" in results
        assert "semantic" in results
    
    @pytest.mark.asyncio
    async def test_log_experience(self, memory_manager):
        episode = await memory_manager.log_experience(
            action="Test action",
            context={"key": "value"},
            outcome="Success",
            success=True,
            lessons=["Lesson 1"],
        )
        assert episode.success is True
    
    @pytest.mark.asyncio
    async def test_stats(self, memory_manager):
        await memory_manager.remember("key1", "value1", MemoryType.SESSION)
        stats = memory_manager.get_stats()
        assert "session" in stats
        assert "long_term" in stats
        assert "episodic" in stats
        assert "semantic" in stats
