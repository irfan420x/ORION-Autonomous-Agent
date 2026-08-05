"""
ORION Memory Contracts
======================

Pydantic models for the 4-Tier Memory Architecture.

Memory Types:
- Session Memory: Short-term, in-memory, per-conversation
- Long-term Memory: Persistent, SQLite-backed, searchable
- Episodic Memory: Experience logs, success/failure patterns
- Semantic Memory: Vector-based, similarity search
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum


class MemoryType(str, Enum):
    """Types of memory in ORION's architecture."""
    SESSION = "SESSION"
    LONG_TERM = "LONG_TERM"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"


class MemoryEntry(BaseModel):
    """A single memory entry."""
    key: str = Field(..., description="Unique key for the memory")
    value: Any = Field(..., description="The memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: float = Field(..., description="Unix timestamp of creation")
    updated_at: float = Field(..., description="Unix timestamp of last update")
    access_count: int = Field(0, description="Number of times accessed")
    importance: float = Field(1.0, description="Importance score (0.0-1.0)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class MemoryQuery(BaseModel):
    """Query for searching memories."""
    query: str = Field(..., description="Search query")
    memory_types: Optional[List[MemoryType]] = Field(None, description="Filter by memory types")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(10, description="Maximum results")
    min_importance: float = Field(0.0, description="Minimum importance score")
    time_range: Optional[Dict[str, float]] = Field(None, description="Time range filter")


class MemorySearchResult(BaseModel):
    """Result from a memory search."""
    entry: MemoryEntry = Field(..., description="The memory entry")
    score: float = Field(..., description="Relevance score (0.0-1.0)")
    match_type: str = Field(..., description="Type of match (exact, semantic, fuzzy)")


class Episode(BaseModel):
    """An episode in episodic memory."""
    episode_id: str = Field(..., description="Unique episode identifier")
    action: str = Field(..., description="What action was taken")
    context: Dict[str, Any] = Field(..., description="Context when action was taken")
    outcome: str = Field(..., description="Result of the action")
    success: bool = Field(..., description="Whether the action was successful")
    lessons_learned: List[str] = Field(default_factory=list, description="Lessons from this episode")
    timestamp: float = Field(..., description="When the episode occurred")
    related_memories: List[str] = Field(default_factory=list, description="Keys of related memories")


class MemoryStats(BaseModel):
    """Statistics about memory usage."""
    total_entries: int = Field(0, description="Total memory entries")
    entries_by_type: Dict[str, int] = Field(default_factory=dict, description="Entries per type")
    total_size_bytes: int = Field(0, description="Total size in bytes")
    avg_access_count: float = Field(0.0, description="Average access count")
    most_accessed: Optional[str] = Field(None, description="Most accessed memory key")
    oldest_entry: Optional[float] = Field(None, description="Timestamp of oldest entry")
    newest_entry: Optional[float] = Field(None, description="Timestamp of newest entry")


class MemoryConfig(BaseModel):
    """Configuration for memory system."""
    session_max_size: int = Field(1000, description="Max entries in session memory")
    session_ttl_seconds: int = Field(3600, description="Session memory TTL")
    long_term_db_path: str = Field("state/memory.db", description="SQLite database path")
    episodic_max_episodes: int = Field(10000, description="Max episodes to store")
    semantic_embedding_dim: int = Field(384, description="Embedding dimension for semantic memory")
    auto_cleanup_enabled: bool = Field(True, description="Enable automatic cleanup")
    cleanup_interval_seconds: int = Field(300, description="Cleanup interval")
