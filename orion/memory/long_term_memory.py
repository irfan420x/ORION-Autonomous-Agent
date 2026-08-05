"""
ORION Long-term Memory
======================

Persistent memory backed by SQLite with FTS5 full-text search.

Features:
- SQLite storage with WAL mode for concurrency
- FTS5 full-text search for fast text queries
- Importance-based ranking
- Tag-based filtering
- Automatic cleanup of old, low-importance entries
- Crash-safe with journal mode

Pattern: Self-contained module with error categorization
"""

import asyncio
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.contracts.memory_contracts import (
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
    MemoryStats,
    MemoryType,
)
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Persistent memory backed by SQLite with FTS5 search.
    
    This is the reliable memory tier, used for:
    - User preferences and settings
    - Learned patterns and behaviors
    - Important facts and knowledge
    - Historical data that must survive restarts
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        db_path: str = "state/memory.db",
    ):
        """
        Initialize Long-term Memory.
        
        Args:
            event_bus: EventBus for publishing memory events.
            db_path: Path to SQLite database file.
        """
        self._event_bus = event_bus
        self._db_path = Path(db_path)
        self._db: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_reads: int = 0
        self._total_writes: int = 0
        self._total_searches: int = 0
        
        logger.info("LongTermMemory initialized (db_path=%s)", db_path)
    
    async def start(self) -> None:
        """Start the memory and initialize the database."""
        async with self._lock:
            self._db = self._create_connection()
            self._create_tables()
            logger.info("LongTermMemory started")
    
    async def stop(self) -> None:
        """Stop the memory and close the database."""
        async with self._lock:
            if self._db:
                self._db.close()
                self._db = None
            logger.info("LongTermMemory stopped")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with optimal settings."""
        # Ensure directory exists
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety/speed
        conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        conn.execute("PRAGMA temp_store=MEMORY")  # Temp tables in memory
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        # Main memory table
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                importance REAL DEFAULT 1.0,
                tags TEXT DEFAULT '[]'
            )
        """)
        
        # FTS5 index for full-text search
        self._db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                key,
                value,
                tags,
                content=memories,
                content_rowid=rowid
            )
        """)
        
        # Triggers to keep FTS index in sync
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, key, value, tags)
                VALUES (new.rowid, new.key, new.value, new.tags);
            END
        """)
        
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, value, tags)
                VALUES ('delete', old.rowid, old.key, old.value, old.tags);
            END
        """)
        
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, value, tags)
                VALUES ('delete', old.rowid, old.key, old.value, old.tags);
                INSERT INTO memories_fts(rowid, key, value, tags)
                VALUES (new.rowid, new.key, new.value, new.tags);
            END
        """)
        
        # Index for fast lookups
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type)
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC)
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at DESC)
        """)
        
        self._db.commit()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from memory.
        
        Args:
            key: The key to look up.
            
        Returns:
            The value, or None if not found.
        """
        async with self._lock:
            self._total_reads += 1
            
            cursor = self._db.execute(
                "SELECT value, metadata, tags, access_count FROM memories WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Update access count
            self._db.execute(
                "UPDATE memories SET access_count = access_count + 1 WHERE key = ?",
                (key,)
            )
            self._db.commit()
            
            return json.loads(row['value'])
    
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
            
            value_json = json.dumps(value)
            tags_json = json.dumps(tags or [])
            metadata_json = json.dumps(metadata or {})
            
            self._db.execute("""
                INSERT INTO memories (key, value, memory_type, metadata, created_at, updated_at, importance, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at,
                    importance = excluded.importance,
                    tags = excluded.tags
            """, (key, value_json, MemoryType.LONG_TERM.value, metadata_json, now, now, importance, tags_json))
            
            self._db.commit()
            
            await self._event_bus.publish(Event(
                event_type="memory.longterm.stored",
                payload={"key": key},
                timestamp=now,
                source="long_term_memory",
            ))
            
            logger.debug("Stored key '%s' in long-term memory", key)
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from memory.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if key was found and deleted, False otherwise.
        """
        async with self._lock:
            cursor = self._db.execute("DELETE FROM memories WHERE key = ?", (key,))
            self._db.commit()
            
            deleted = cursor.rowcount > 0
            
            if deleted:
                await self._event_bus.publish(Event(
                    event_type="memory.longterm.deleted",
                    payload={"key": key},
                    timestamp=time.time(),
                    source="long_term_memory",
                ))
            
            return deleted
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        min_importance: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> List[MemorySearchResult]:
        """
        Search memory using full-text search.
        
        Args:
            query: Search query.
            limit: Maximum results.
            min_importance: Minimum importance score.
            tags: Optional tag filter.
            
        Returns:
            List of search results.
        """
        async with self._lock:
            self._total_searches += 1
            
            # Build query
            sql = """
                SELECT m.key, m.value, m.metadata, m.tags, m.created_at, m.updated_at,
                       m.access_count, m.importance,
                       rank
                FROM memories_fts fts
                JOIN memories m ON fts.rowid = m.rowid
                WHERE memories_fts MATCH ?
                  AND m.importance >= ?
            """
            params: list = [query, min_importance]
            
            if tags:
                tag_conditions = " AND ".join(["m.tags LIKE ?" for _ in tags])
                sql += f" AND ({tag_conditions})"
                params.extend([f"%{tag}%" for tag in tags])
            
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)
            
            cursor = self._db.execute(sql, params)
            results = []
            
            for row in cursor.fetchall():
                entry = MemoryEntry(
                    key=row['key'],
                    value=json.loads(row['value']),
                    memory_type=MemoryType.LONG_TERM,
                    metadata=json.loads(row['metadata']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    access_count=row['access_count'],
                    importance=row['importance'],
                    tags=json.loads(row['tags']),
                )
                
                # Normalize FTS5 rank to 0-1 score
                score = 1.0 / (1.0 + abs(row['rank']))
                
                results.append(MemorySearchResult(
                    entry=entry,
                    score=score,
                    match_type="fts5",
                ))
            
            return results
    
    async def get_by_tag(self, tag: str, limit: int = 100) -> List[MemoryEntry]:
        """
        Get all entries with a specific tag.
        
        Args:
            tag: The tag to search for.
            limit: Maximum results.
            
        Returns:
            List of matching entries.
        """
        async with self._lock:
            cursor = self._db.execute(
                "SELECT * FROM memories WHERE tags LIKE ? ORDER BY importance DESC, updated_at DESC LIMIT ?",
                (f"%{tag}%", limit)
            )
            
            entries = []
            for row in cursor.fetchall():
                entries.append(MemoryEntry(
                    key=row['key'],
                    value=json.loads(row['value']),
                    memory_type=MemoryType.LONG_TERM,
                    metadata=json.loads(row['metadata']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    access_count=row['access_count'],
                    importance=row['importance'],
                    tags=json.loads(row['tags']),
                ))
            
            return entries
    
    async def get_all(self, limit: int = 1000) -> List[MemoryEntry]:
        """
        Get all entries.
        
        Args:
            limit: Maximum results.
            
        Returns:
            List of all entries.
        """
        async with self._lock:
            cursor = self._db.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
            
            entries = []
            for row in cursor.fetchall():
                entries.append(MemoryEntry(
                    key=row['key'],
                    value=json.loads(row['value']),
                    memory_type=MemoryType.LONG_TERM,
                    metadata=json.loads(row['metadata']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    access_count=row['access_count'],
                    importance=row['importance'],
                    tags=json.loads(row['tags']),
                ))
            
            return entries
    
    async def cleanup_old_entries(self, max_age_days: int = 30, min_importance: float = 0.3) -> int:
        """
        Remove old, low-importance entries.
        
        Args:
            max_age_days: Maximum age in days.
            min_importance: Minimum importance to keep.
            
        Returns:
            Number of entries removed.
        """
        async with self._lock:
            cutoff = time.time() - (max_age_days * 86400)
            
            cursor = self._db.execute(
                "DELETE FROM memories WHERE updated_at < ? AND importance < ?",
                (cutoff, min_importance)
            )
            self._db.commit()
            
            removed = cursor.rowcount
            if removed:
                logger.info("Cleaned up %d old entries", removed)
            
            return removed
    
    async def clear(self) -> int:
        """
        Clear all entries.
        
        Returns:
            Number of entries cleared.
        """
        async with self._lock:
            cursor = self._db.execute("SELECT COUNT(*) FROM memories")
            count = cursor.fetchone()[0]
            self._db.execute("DELETE FROM memories")
            self._db.commit()
            logger.info("Cleared %d entries from long-term memory", count)
            return count
    
    def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        cursor = self._db.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(access_count) as avg_access,
                MIN(created_at) as oldest,
                MAX(updated_at) as newest,
                SUM(LENGTH(value)) as total_size
            FROM memories
        """)
        row = cursor.fetchone()
        
        # Get most accessed
        most_accessed_cursor = self._db.execute(
            "SELECT key FROM memories ORDER BY access_count DESC LIMIT 1"
        )
        most_accessed_row = most_accessed_cursor.fetchone()
        
        # Get count by type
        type_cursor = self._db.execute(
            "SELECT memory_type, COUNT(*) as cnt FROM memories GROUP BY memory_type"
        )
        entries_by_type = {row['memory_type']: row['cnt'] for row in type_cursor.fetchall()}
        
        return MemoryStats(
            total_entries=row['total'] or 0,
            entries_by_type=entries_by_type,
            total_size_bytes=row['total_size'] or 0,
            avg_access_count=row['avg_access'] or 0.0,
            most_accessed=most_accessed_row['key'] if most_accessed_row else None,
            oldest_entry=row['oldest'],
            newest_entry=row['newest'],
        )
    
    def get_internal_stats(self) -> Dict[str, Any]:
        """Get internal statistics for debugging."""
        return {
            "db_path": str(self._db_path),
            "total_reads": self._total_reads,
            "total_writes": self._total_writes,
            "total_searches": self._total_searches,
        }
