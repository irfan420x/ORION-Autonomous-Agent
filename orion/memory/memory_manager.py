"""
ORION Memory Manager
====================

Unified interface for the 4-Tier Memory Architecture.

Features:
- Unified API for all memory tiers
- Automatic tier selection based on data type
- Cross-tier search
- Memory consolidation
- Statistics and monitoring

Pattern: Facade pattern for memory subsystem
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.contracts.memory_contracts import (
    Episode,
    MemoryConfig,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
    MemoryStats,
    MemoryType,
)
from orion.core.communication.event_bus import EventBus
from orion.memory.session_memory import SessionMemory
from orion.memory.long_term_memory import LongTermMemory
from orion.memory.episodic_memory import EpisodicMemory
from orion.memory.semantic_memory import SemanticMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Unified interface for ORION's 4-Tier Memory Architecture.
    
    Tiers:
    1. Session Memory: Fast, in-memory, LRU eviction
    2. Long-term Memory: Persistent, SQLite, FTS5 search
    3. Episodic Memory: Experience logging, pattern recognition
    4. Semantic Memory: Vector search, RAG support
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        config: Optional[MemoryConfig] = None,
    ):
        """
        Initialize Memory Manager.
        
        Args:
            event_bus: EventBus for publishing events.
            config: Optional memory configuration.
        """
        self._event_bus = event_bus
        self._config = config or MemoryConfig()
        
        # Initialize memory tiers
        self.session = SessionMemory(
            event_bus=event_bus,
            max_size=self._config.session_max_size,
            ttl_seconds=self._config.session_ttl_seconds,
        )
        
        self.long_term = LongTermMemory(
            event_bus=event_bus,
            db_path=self._config.long_term_db_path,
        )
        
        self.episodic = EpisodicMemory(
            event_bus=event_bus,
            max_episodes=self._config.episodic_max_episodes,
        )
        
        self.semantic = SemanticMemory(
            event_bus=event_bus,
            dimension=self._config.semantic_embedding_dim,
        )
        
        self._lock = asyncio.Lock()
        
        logger.info("MemoryManager initialized")
    
    async def start(self) -> None:
        """Start all memory tiers."""
        await self.long_term.start()
        logger.info("MemoryManager started")
    
    async def stop(self) -> None:
        """Stop all memory tiers."""
        await self.long_term.stop()
        logger.info("MemoryManager stopped")
    
    # ========================================================================
    # Unified API
    # ========================================================================
    
    async def remember(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.SESSION,
        importance: float = 1.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a memory in the specified tier.
        
        Args:
            key: Memory key.
            value: Memory value.
            memory_type: Which tier to store in.
            importance: Importance score (0.0-1.0).
            tags: Optional tags.
            metadata: Optional metadata.
        """
        if memory_type == MemoryType.SESSION:
            await self.session.put(key, value, importance, tags, metadata)
        elif memory_type == MemoryType.LONG_TERM:
            await self.long_term.put(key, value, importance, tags, metadata)
        elif memory_type == MemoryType.SEMANTIC:
            if isinstance(value, str):
                await self.semantic.add_document(key, value, metadata)
            else:
                # Store non-string values in long-term memory
                await self.long_term.put(key, value, importance, tags, metadata)
        
        await self._event_bus.publish(Event(
            event_type="memory.remembered",
            payload={"key": key, "type": memory_type.value},
            timestamp=time.time(),
            source="memory_manager",
        ))
    
    async def recall(
        self,
        key: str,
        memory_type: MemoryType = MemoryType.SESSION,
    ) -> Optional[Any]:
        """
        Recall a memory from the specified tier.
        
        Args:
            key: Memory key.
            memory_type: Which tier to look in.
            
        Returns:
            The memory value, or None if not found.
        """
        if memory_type == MemoryType.SESSION:
            return await self.session.get(key)
        elif memory_type == MemoryType.LONG_TERM:
            return await self.long_term.get(key)
        elif memory_type == MemoryType.SEMANTIC:
            doc = await self.semantic.get_document(key)
            return doc['content'] if doc else None
        
        return None
    
    async def recall_all_tiers(self, key: str) -> Optional[Any]:
        """
        Try to recall from all tiers (session first, then long-term).
        
        Args:
            key: Memory key.
            
        Returns:
            The memory value, or None if not found in any tier.
        """
        # Try session first (fastest)
        result = await self.session.get(key)
        if result is not None:
            return result
        
        # Try long-term
        result = await self.long_term.get(key)
        if result is not None:
            # Promote to session for faster access
            await self.session.put(key, result)
            return result
        
        return None
    
    async def forget(
        self,
        key: str,
        memory_type: Optional[MemoryType] = None,
    ) -> bool:
        """
        Delete a memory from specified tier or all tiers.
        
        Args:
            key: Memory key.
            memory_type: Which tier to delete from. None = all tiers.
            
        Returns:
            True if memory was found and deleted.
        """
        deleted = False
        
        if memory_type is None or memory_type == MemoryType.SESSION:
            if await self.session.delete(key):
                deleted = True
        
        if memory_type is None or memory_type == MemoryType.LONG_TERM:
            if await self.long_term.delete(key):
                deleted = True
        
        if memory_type is None or memory_type == MemoryType.SEMANTIC:
            if await self.semantic.delete_document(key):
                deleted = True
        
        return deleted
    
    async def search_all(
        self,
        query: str,
        limit: int = 10,
    ) -> Dict[str, List]:
        """
        Search across all memory tiers.
        
        Args:
            query: Search query.
            limit: Maximum results per tier.
            
        Returns:
            Dictionary with results from each tier.
        """
        session_results = await self.session.search(query, limit)
        long_term_results = await self.long_term.search(query, limit)
        semantic_results = await self.semantic.search(query, limit)
        
        return {
            "session": session_results,
            "long_term": [r.entry for r in long_term_results],
            "semantic": semantic_results,
        }
    
    # ========================================================================
    # Episodic Memory API
    # ========================================================================
    
    async def log_experience(
        self,
        action: str,
        context: Dict[str, Any],
        outcome: str,
        success: bool,
        lessons: Optional[List[str]] = None,
    ) -> Episode:
        """
        Log an experience to episodic memory.
        
        Args:
            action: What action was taken.
            context: Context when action was taken.
            outcome: Result of the action.
            success: Whether the action was successful.
            lessons: Lessons learned.
            
        Returns:
            The created episode.
        """
        return await self.episodic.log_episode(
            action=action,
            context=context,
            outcome=outcome,
            success=success,
            lessons_learned=lessons,
        )
    
    async def get_similar_experiences(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 5,
    ) -> List[Episode]:
        """
        Find similar past experiences.
        
        Args:
            action: The action to find similar experiences for.
            context: Optional context to match.
            limit: Maximum results.
            
        Returns:
            List of similar episodes.
        """
        return await self.episodic.get_similar_episodes(action, context, limit)
    
    async def learn_from_failures(self) -> List[str]:
        """
        Get lessons learned from failures.
        
        Returns:
            List of lessons.
        """
        return await self.episodic.get_lessons()
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all memory tiers."""
        return {
            "session": self.session.get_stats().model_dump(),
            "long_term": self.long_term.get_stats().model_dump(),
            "episodic": self.episodic.get_stats(),
            "semantic": self.semantic.get_stats(),
        }
    
    async def cleanup(self) -> Dict[str, int]:
        """
        Run cleanup on all tiers.
        
        Returns:
            Number of items cleaned up per tier.
        """
        session_cleaned = await self.session.cleanup_expired()
        long_term_cleaned = await self.long_term.cleanup_old_entries()
        
        return {
            "session": session_cleaned,
            "long_term": long_term_cleaned,
        }
