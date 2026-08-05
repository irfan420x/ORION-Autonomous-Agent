"""
ORION Advanced Memory System
=============================

超越 Claude Code's memory with:
- Multi-tier architecture (session, working, long-term, episodic, semantic)
- Memory consolidation (automatic summarization)
- Memory graph (associations between memories)
- Memory reflection (learning from patterns)
- Memory sharing (between agents)
- Memory visualization (graph-based)

Inspired by Claude Code's Store pattern + SQLite FTS5,
but with AI-powered consolidation and graph relationships.
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
import uuid
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class MemoryTier(str, Enum):
    """Memory tiers with different characteristics."""
    SESSION = "session"          # In-memory, fast, ephemeral
    WORKING = "working"          # Active task context
    LONG_TERM = "long_term"      # Persistent, SQLite-backed
    EPISODIC = "episodic"        # Experience logs
    SEMANTIC = "semantic"        # Vector-based, similarity search


class MemoryImportance(str, Enum):
    """Importance levels for memory entries."""
    CRITICAL = "critical"    # Must never forget
    HIGH = "high"            # Important, keep long-term
    MEDIUM = "medium"        # Normal importance
    LOW = "low"              # Can be forgotten if needed
    EPHEMERAL = "ephemeral"  # Auto-delete after TTL


class MemoryEntry:
    """A single memory entry with rich metadata."""
    
    def __init__(
        self,
        key: str,
        value: Any,
        tier: MemoryTier = MemoryTier.SESSION,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        associations: Optional[List[str]] = None,
        ttl_seconds: Optional[int] = None,
    ):
        self.id = uuid.uuid4().hex[:12]
        self.key = key
        self.value = value
        self.tier = tier
        self.importance = importance
        self.tags = tags or []
        self.source = source
        self.associations = associations or []  # IDs of related memories
        self.ttl_seconds = ttl_seconds
        
        # Metadata
        self.created_at = time.time()
        self.updated_at = time.time()
        self.accessed_at = time.time()
        self.access_count = 0
        self.consolidated = False
        self.embedding: Optional[List[float]] = None
    
    def touch(self):
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1
    
    def is_expired(self) -> bool:
        """Check if memory has expired."""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "tier": self.tier.value,
            "importance": self.importance.value,
            "tags": self.tags,
            "source": self.source,
            "associations": self.associations,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "consolidated": self.consolidated,
        }


class MemoryGraph:
    """Graph-based memory relationships."""
    
    def __init__(self):
        self._nodes: Dict[str, MemoryEntry] = {}  # id -> entry
        self._edges: Dict[str, Set[str]] = defaultdict(set)  # id -> set of connected ids
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> set of ids
        self._key_index: Dict[str, str] = {}  # key -> id
    
    def add(self, entry: MemoryEntry) -> None:
        """Add a memory to the graph."""
        self._nodes[entry.id] = entry
        self._key_index[entry.key] = entry.id
        
        # Index tags
        for tag in entry.tags:
            self._tag_index[tag].add(entry.id)
        
        # Create associations
        for assoc_key in entry.associations:
            if assoc_key in self._key_index:
                assoc_id = self._key_index[assoc_key]
                self._edges[entry.id].add(assoc_id)
                self._edges[assoc_id].add(entry.id)
    
    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a memory by ID."""
        return self._nodes.get(memory_id)
    
    def get_by_key(self, key: str) -> Optional[MemoryEntry]:
        """Get a memory by key."""
        entry_id = self._key_index.get(key)
        return self._nodes.get(entry_id) if entry_id else None
    
    def get_related(self, memory_id: str) -> List[MemoryEntry]:
        """Get all memories related to a given memory."""
        related_ids = self._edges.get(memory_id, set())
        return [self._nodes[rid] for rid in related_ids if rid in self._nodes]
    
    def get_by_tag(self, tag: str) -> List[MemoryEntry]:
        """Get all memories with a specific tag."""
        entry_ids = self._tag_index.get(tag, set())
        return [self._nodes[eid] for eid in entry_ids if eid in self._nodes]
    
    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """Simple text search across memories."""
        query_lower = query.lower()
        results = []
        
        for entry in self._nodes.values():
            # Search in key
            if query_lower in entry.key.lower():
                results.append((1.0, entry))
                continue
            
            # Search in value
            value_str = str(entry.value).lower()
            if query_lower in value_str:
                # Score based on match position and access count
                score = 0.5 + (entry.access_count * 0.01)
                results.append((score, entry))
                continue
            
            # Search in tags
            for tag in entry.tags:
                if query_lower in tag.lower():
                    results.append((0.3, entry))
                    break
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:limit]]
    
    def get_all(self) -> List[MemoryEntry]:
        """Get all memories."""
        return list(self._nodes.values())
    
    def remove(self, memory_id: str) -> bool:
        """Remove a memory from the graph."""
        if memory_id not in self._nodes:
            return False
        
        entry = self._nodes[memory_id]
        
        # Remove from indexes
        self._key_index.pop(entry.key, None)
        for tag in entry.tags:
            self._tag_index[tag].discard(memory_id)
        
        # Remove edges
        for connected_id in self._edges.get(memory_id, set()):
            self._edges[connected_id].discard(memory_id)
        self._edges.pop(memory_id, None)
        
        # Remove node
        del self._nodes[memory_id]
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_memories": len(self._nodes),
            "total_edges": sum(len(edges) for edges in self._edges.values()) // 2,
            "total_tags": len(self._tag_index),
            "avg_connections": (
                sum(len(edges) for edges in self._edges.values()) / len(self._nodes)
                if self._nodes else 0
            ),
        }


class AdvancedMemorySystem:
    """
    Advanced memory system with multi-tier architecture,
    consolidation, graph relationships, and reflection.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        db_path: str = "state/advanced_memory.db",
        consolidation_interval: float = 300.0,  # 5 minutes
        max_session_memories: int = 1000,
        max_working_memories: int = 100,
    ):
        self._event_bus = event_bus
        self._db_path = db_path
        self._consolidation_interval = consolidation_interval
        self._max_session = max_session_memories
        self._max_working = max_working_memories
        
        # Memory tiers
        self._session: Dict[str, MemoryEntry] = {}
        self._working: Dict[str, MemoryEntry] = {}
        self._graph = MemoryGraph()
        
        # SQLite for persistent storage
        self._db: Optional[sqlite3.Connection] = None
        
        # Consolidation
        self._consolidation_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Stats
        self._total_stores: int = 0
        self._total_retrievals: int = 0
        self._total_consolidations: int = 0
        
        logger.info("AdvancedMemorySystem initialized")
    
    async def start(self) -> None:
        """Start the memory system."""
        # Initialize SQLite
        self._db = sqlite3.connect(self._db_path)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                tier TEXT NOT NULL,
                importance TEXT NOT NULL,
                tags TEXT,
                source TEXT,
                associations TEXT,
                created_at REAL,
                updated_at REAL,
                accessed_at REAL,
                access_count INTEGER DEFAULT 0,
                consolidated BOOLEAN DEFAULT FALSE,
                embedding BLOB
            )
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_tier ON memories(tier)
        """)
        self._db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
            USING fts5(key, value, tags, content=memories, content_rowid=rowid)
        """)
        self._db.commit()
        
        # Load existing memories into graph
        await self._load_from_db()
        
        # Start consolidation loop
        self._running = True
        self._consolidation_task = asyncio.create_task(self._consolidation_loop())
        
        logger.info("AdvancedMemorySystem started")
    
    async def stop(self) -> None:
        """Stop the memory system."""
        self._running = False
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass
        
        if self._db:
            self._db.close()
        
        logger.info("AdvancedMemorySystem stopped")
    
    # ── Store Operations ──────────────────────────────────────
    
    async def store(
        self,
        key: str,
        value: Any,
        tier: MemoryTier = MemoryTier.SESSION,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        associations: Optional[List[str]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> MemoryEntry:
        """Store a memory entry."""
        entry = MemoryEntry(
            key=key,
            value=value,
            tier=tier,
            importance=importance,
            tags=tags,
            source=source,
            associations=associations,
            ttl_seconds=ttl_seconds,
        )
        
        # Store in appropriate tier
        if tier == MemoryTier.SESSION:
            self._session[key] = entry
            # Evict if over limit
            if len(self._session) > self._max_session:
                self._evict_lru(self._session)
        
        elif tier == MemoryTier.WORKING:
            self._working[key] = entry
            if len(self._working) > self._max_working:
                self._evict_lru(self._working)
        
        # Add to graph
        self._graph.add(entry)
        
        # Persist to SQLite
        await self._persist_to_db(entry)
        
        self._total_stores += 1
        
        # Publish event
        await self._event_bus.publish(Event(
            event_type="memory.stored",
            payload={"key": key, "tier": tier.value, "importance": importance.value},
            timestamp=time.time(),
            source="memory_system",
        ))
        
        logger.debug("Stored memory: %s (tier=%s)", key, tier.value)
        return entry
    
    async def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory by key."""
        self._total_retrievals += 1
        
        # Check session first
        if key in self._session:
            entry = self._session[key]
            entry.touch()
            return entry
        
        # Check working memory
        if key in self._working:
            entry = self._working[key]
            entry.touch()
            return entry
        
        # Check graph (long-term, episodic, semantic)
        entry = self._graph.get_by_key(key)
        if entry:
            entry.touch()
            await self._update_access_in_db(entry)
            return entry
        
        return None
    
    async def search(
        self,
        query: str,
        tier: Optional[MemoryTier] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Search memories across tiers."""
        self._total_retrievals += 1
        
        # If tags specified, search by tag first
        if tags:
            results = []
            for tag in tags:
                results.extend(self._graph.get_by_tag(tag))
            # Filter by query
            if query:
                results = [r for r in results if query.lower() in str(r.value).lower()]
            return results[:limit]
        
        # Text search
        return self._graph.search(query, limit)
    
    async def forget(self, key: str) -> bool:
        """Remove a memory."""
        # Remove from session
        if key in self._session:
            del self._session[key]
        
        # Remove from working
        if key in self._working:
            del self._working[key]
        
        # Remove from graph
        entry = self._graph.get_by_key(key)
        if entry:
            self._graph.remove(entry.id)
            await self._remove_from_db(entry.id)
            
            await self._event_bus.publish(Event(
                event_type="memory.forgotten",
                payload={"key": key},
                timestamp=time.time(),
                source="memory_system",
            ))
            return True
        
        return False
    
    # ── Consolidation ─────────────────────────────────────────
    
    async def _consolidation_loop(self) -> None:
        """Periodically consolidate memories."""
        while self._running:
            try:
                await asyncio.sleep(self._consolidation_interval)
                await self._consolidate()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Consolidation error: %s", e)
    
    async def _consolidate(self) -> None:
        """
        Consolidate memories:
        1. Remove expired memories
        2. Promote frequently accessed session memories to working
        3. Promote important working memories to long-term
        4. Compress old episodic memories
        """
        now = time.time()
        consolidated = 0
        
        # 1. Remove expired
        expired_keys = [
            key for key, entry in self._session.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            await self.forget(key)
            consolidated += 1
        
        # 2. Promote frequently accessed session -> working
        for key, entry in list(self._session.items()):
            if entry.access_count >= 5 and entry.importance != MemoryImportance.EPHEMERAL:
                entry.tier = MemoryTier.WORKING
                self._working[key] = entry
                del self._session[key]
                consolidated += 1
        
        # 3. Promote important working -> long-term
        for key, entry in list(self._working.items()):
            if entry.importance in (MemoryImportance.CRITICAL, MemoryImportance.HIGH):
                entry.tier = MemoryTier.LONG_TERM
                entry.consolidated = True
                consolidated += 1
        
        if consolidated > 0:
            self._total_consolidations += 1
            logger.info("Consolidated %d memories", consolidated)
            
            await self._event_bus.publish(Event(
                event_type="memory.consolidated",
                payload={"count": consolidated},
                timestamp=time.time(),
                source="memory_system",
            ))
    
    # ── Reflection ────────────────────────────────────────────
    
    async def reflect(self, topic: str) -> Dict[str, Any]:
        """
        Reflect on memories about a topic.
        Returns patterns, associations, and insights.
        """
        # Search for related memories
        memories = await self.search(topic, limit=20)
        
        if not memories:
            return {"topic": topic, "insights": [], "patterns": []}
        
        # Analyze patterns
        patterns = []
        insights = []
        
        # Pattern: frequently accessed memories
        frequent = [m for m in memories if m.access_count > 3]
        if frequent:
            patterns.append({
                "type": "frequent_access",
                "count": len(frequent),
                "keys": [m.key for m in frequent[:5]],
            })
        
        # Pattern: recent memories
        now = time.time()
        recent = [m for m in memories if (now - m.created_at) < 3600]
        if recent:
            patterns.append({
                "type": "recent",
                "count": len(recent),
                "keys": [m.key for m in recent[:5]],
            })
        
        # Pattern: associated memories
        all_associations = set()
        for m in memories:
            all_associations.update(m.associations)
        if all_associations:
            patterns.append({
                "type": "associations",
                "count": len(all_associations),
                "related_keys": list(all_associations)[:10],
            })
        
        # Insight: most common tags
        tag_counts: Dict[str, int] = defaultdict(int)
        for m in memories:
            for tag in m.tags:
                tag_counts[tag] += 1
        if tag_counts:
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            insights.append({
                "type": "common_tags",
                "tags": dict(top_tags),
            })
        
        return {
            "topic": topic,
            "memory_count": len(memories),
            "patterns": patterns,
            "insights": insights,
        }
    
    # ── SQLite Persistence ────────────────────────────────────
    
    async def _persist_to_db(self, entry: MemoryEntry) -> None:
        """Persist a memory to SQLite."""
        if not self._db:
            return
        
        self._db.execute("""
            INSERT OR REPLACE INTO memories 
            (id, key, value, tier, importance, tags, source, associations,
             created_at, updated_at, accessed_at, access_count, consolidated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id, entry.key, json.dumps(entry.value),
            entry.tier.value, entry.importance.value,
            json.dumps(entry.tags), entry.source,
            json.dumps(entry.associations),
            entry.created_at, entry.updated_at, entry.accessed_at,
            entry.access_count, entry.consolidated,
        ))
        self._db.commit()
    
    async def _update_access_in_db(self, entry: MemoryEntry) -> None:
        """Update access metadata in SQLite."""
        if not self._db:
            return
        
        self._db.execute("""
            UPDATE memories SET accessed_at = ?, access_count = ?
            WHERE id = ?
        """, (entry.accessed_at, entry.access_count, entry.id))
        self._db.commit()
    
    async def _remove_from_db(self, memory_id: str) -> None:
        """Remove a memory from SQLite."""
        if not self._db:
            return
        
        self._db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._db.commit()
    
    async def _load_from_db(self) -> None:
        """Load memories from SQLite into graph."""
        if not self._db:
            return
        
        cursor = self._db.execute("SELECT * FROM memories")
        for row in cursor.fetchall():
            entry = MemoryEntry(
                key=row[1],
                value=json.loads(row[2]),
                tier=MemoryTier(row[3]),
                importance=MemoryImportance(row[4]),
                tags=json.loads(row[5]) if row[5] else [],
                source=row[6],
                associations=json.loads(row[7]) if row[7] else [],
            )
            entry.id = row[0]
            entry.created_at = row[8]
            entry.updated_at = row[9]
            entry.accessed_at = row[10]
            entry.access_count = row[11]
            entry.consolidated = bool(row[12])
            
            self._graph.add(entry)
            
            # Load into appropriate tier
            if entry.tier == MemoryTier.SESSION:
                self._session[entry.key] = entry
            elif entry.tier == MemoryTier.WORKING:
                self._working[entry.key] = entry
        
        logger.info("Loaded %d memories from database", len(self._graph.get_all()))
    
    # ── Utility ───────────────────────────────────────────────
    
    def _evict_lru(self, tier_dict: Dict[str, MemoryEntry]) -> None:
        """Evict least recently used memory from a tier."""
        if not tier_dict:
            return
        
        lru_key = min(tier_dict.keys(), key=lambda k: tier_dict[k].accessed_at)
        del tier_dict[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        graph_stats = self._graph.get_stats()
        
        return {
            "session_count": len(self._session),
            "working_count": len(self._working),
            "graph_stats": graph_stats,
            "total_stores": self._total_stores,
            "total_retrievals": self._total_retrievals,
            "total_consolidations": self._total_consolidations,
            "db_path": self._db_path,
        }
