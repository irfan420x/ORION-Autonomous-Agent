"""
ORION Session Memory
====================

Short-term, in-memory storage with LRU eviction.

Features:
- LRU (Least Recently Used) eviction when capacity is reached
- TTL (Time To Live) for automatic expiration
- Thread-safe operations
- Event publishing on memory changes
- Access count tracking

Pattern: Minimal Store (from Claude Code source analysis)
"""

import asyncio
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Set

from orion.contracts.agent_contracts import Event
from orion.contracts.memory_contracts import MemoryEntry, MemoryType, MemoryStats
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class SessionMemory:
    """
    In-memory session storage with LRU eviction.
    
    This is the fastest memory tier, used for:
    - Current conversation context
    - Temporary computation results
    - Hot data that's accessed frequently
    
    Uses OrderedDict for O(1) LRU operations.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        max_size: int = 1000,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize Session Memory.
        
        Args:
            event_bus: EventBus for publishing memory events.
            max_size: Maximum number of entries.
            ttl_seconds: Time-to-live for entries in seconds.
        """
        self._event_bus = event_bus
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        
        # OrderedDict for LRU: newest at end, oldest at start
        self._entries: OrderedDict[str, MemoryEntry] = OrderedDict()
        
        # Indexes for fast lookup
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> set of keys
        
        # Statistics
        self._total_reads: int = 0
        self._total_writes: int = 0
        self._total_evictions: int = 0
        
        self._lock = asyncio.Lock()
        
        logger.info("SessionMemory initialized (max_size=%d, ttl=%ds)", max_size, ttl_seconds)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from memory.
        
        Args:
            key: The key to look up.
            
        Returns:
            The value, or None if not found or expired.
        """
        async with self._lock:
            self._total_reads += 1
            
            if key not in self._entries:
                return None
            
            entry = self._entries[key]
            
            # Check TTL
            if self._is_expired(entry):
                await self._remove_internal(key)
                return None
            
            # Move to end (most recently used)
            self._entries.move_to_end(key)
            entry.access_count += 1
            
            return entry.value
    
    async def put(
        self,
        key: str,
        value: Any,
        importance: float = 1.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a value in memory.
        
        Args:
            key: The key to store under.
            value: The value to store.
            importance: Importance score (0.0-1.0).
            tags: Optional tags for categorization.
            metadata: Optional additional metadata.
        """
        async with self._lock:
            self._total_writes += 1
            now = time.time()
            
            # Update existing entry
            if key in self._entries:
                old_entry = self._entries[key]
                # Remove old tags from index
                self._remove_from_tag_index(key, old_entry.tags)
                
                old_entry.value = value
                old_entry.updated_at = now
                old_entry.importance = importance
                old_entry.tags = tags or []
                old_entry.metadata = metadata or {}
                
                # Add new tags to index
                self._add_to_tag_index(key, old_entry.tags)
                
                # Move to end
                self._entries.move_to_end(key)
                
                await self._event_bus.publish(Event(
                    event_type="memory.session.updated",
                    payload={"key": key},
                    timestamp=now,
                    source="session_memory",
                ))
                return
            
            # Evict if at capacity
            while len(self._entries) >= self._max_size:
                await self._evict_lru()
            
            # Create new entry
            entry = MemoryEntry(
                key=key,
                value=value,
                memory_type=MemoryType.SESSION,
                metadata=metadata or {},
                created_at=now,
                updated_at=now,
                access_count=0,
                importance=importance,
                tags=tags or [],
            )
            
            self._entries[key] = entry
            self._add_to_tag_index(key, entry.tags)
            
            await self._event_bus.publish(Event(
                event_type="memory.session.created",
                payload={"key": key},
                timestamp=now,
                source="session_memory",
            ))
            
            logger.debug("Stored key '%s' in session memory", key)
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from memory.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if key was found and deleted, False otherwise.
        """
        async with self._lock:
            if key not in self._entries:
                return False
            
            await self._remove_internal(key)
            return True
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        async with self._lock:
            if key not in self._entries:
                return False
            
            if self._is_expired(self._entries[key]):
                await self._remove_internal(key)
                return False
            
            return True
    
    async def get_by_tag(self, tag: str) -> List[MemoryEntry]:
        """
        Get all entries with a specific tag.
        
        Args:
            tag: The tag to search for.
            
        Returns:
            List of matching entries.
        """
        async with self._lock:
            keys = self._tag_index.get(tag, set())
            entries = []
            
            for key in list(keys):
                if key in self._entries:
                    entry = self._entries[key]
                    if not self._is_expired(entry):
                        entries.append(entry)
            
            return entries
    
    async def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """
        Simple text search in memory keys and values.
        
        Args:
            query: Search query.
            limit: Maximum results.
            
        Returns:
            List of matching entries.
        """
        async with self._lock:
            results = []
            query_lower = query.lower()
            
            for entry in self._entries.values():
                if self._is_expired(entry):
                    continue
                
                # Search in key
                if query_lower in entry.key.lower():
                    results.append(entry)
                    continue
                
                # Search in value (if string)
                if isinstance(entry.value, str) and query_lower in entry.value.lower():
                    results.append(entry)
                    continue
                
                # Search in tags
                if any(query_lower in tag.lower() for tag in entry.tags):
                    results.append(entry)
            
            return results[:limit]
    
    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed.
        """
        async with self._lock:
            expired_keys = [
                key for key, entry in self._entries.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                await self._remove_internal(key)
            
            if expired_keys:
                logger.info("Cleaned up %d expired entries", len(expired_keys))
            
            return len(expired_keys)
    
    async def clear(self) -> int:
        """
        Clear all entries.
        
        Returns:
            Number of entries cleared.
        """
        async with self._lock:
            count = len(self._entries)
            self._entries.clear()
            self._tag_index.clear()
            logger.info("Cleared %d entries from session memory", count)
            return count
    
    def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        now = time.time()
        valid_entries = [
            e for e in self._entries.values()
            if not self._is_expired(e, now)
        ]
        
        return MemoryStats(
            total_entries=len(valid_entries),
            entries_by_type={"SESSION": len(valid_entries)},
            total_size_bytes=sum(
                len(str(e.value)) for e in valid_entries
            ),
            avg_access_count=(
                sum(e.access_count for e in valid_entries) / len(valid_entries)
                if valid_entries else 0.0
            ),
            most_accessed=(
                max(valid_entries, key=lambda e: e.access_count).key
                if valid_entries else None
            ),
            oldest_entry=(
                min(e.created_at for e in valid_entries)
                if valid_entries else None
            ),
            newest_entry=(
                max(e.updated_at for e in valid_entries)
                if valid_entries else None
            ),
        )
    
    def _is_expired(self, entry: MemoryEntry, now: Optional[float] = None) -> bool:
        """Check if an entry is expired."""
        if self._ttl_seconds <= 0:
            return False
        now = now or time.time()
        return (now - entry.updated_at) > self._ttl_seconds
    
    async def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._entries:
            return
        
        # Get oldest (first) key
        key = next(iter(self._entries))
        await self._remove_internal(key)
        self._total_evictions += 1
        
        logger.debug("Evicted LRU key '%s'", key)
    
    async def _remove_internal(self, key: str) -> None:
        """Remove an entry (must hold lock)."""
        if key in self._entries:
            entry = self._entries.pop(key)
            self._remove_from_tag_index(key, entry.tags)
            
            await self._event_bus.publish(Event(
                event_type="memory.session.deleted",
                payload={"key": key},
                timestamp=time.time(),
                source="session_memory",
            ))
    
    def _add_to_tag_index(self, key: str, tags: List[str]) -> None:
        """Add key to tag index."""
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(key)
    
    def _remove_from_tag_index(self, key: str, tags: List[str]) -> None:
        """Remove key from tag index."""
        for tag in tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(key)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
    
    def get_internal_stats(self) -> Dict[str, Any]:
        """Get internal statistics for debugging."""
        return {
            "size": len(self._entries),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl_seconds,
            "total_reads": self._total_reads,
            "total_writes": self._total_writes,
            "total_evictions": self._total_evictions,
            "tag_count": len(self._tag_index),
        }
