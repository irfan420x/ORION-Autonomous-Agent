"""
ORION Semantic Memory
=====================

Vector-based memory for semantic search and RAG.

Features:
- Document storage with embeddings
- Cosine similarity search
- Metadata filtering
- Batch operations
- Mock embedding for MVP (replace with real embeddings later)

Pattern: Strategy pattern for embedding providers
"""

import asyncio
import hashlib
import json
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from orion.contracts.agent_contracts import Event
from orion.contracts.memory_contracts import MemoryEntry, MemoryType
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Base class for embedding providers."""
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        raise NotImplementedError
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        raise NotImplementedError


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock embedding provider for MVP.
    
    Generates deterministic pseudo-embeddings based on text hash.
    Replace with real embeddings (e.g., sentence-transformers) later.
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    async def embed(self, text: str) -> List[float]:
        """Generate a deterministic mock embedding."""
        # Use text hash to generate deterministic "embedding"
        hash_bytes = hashlib.md5(text.encode()).digest()
        
        # Convert to float vector
        embedding = []
        for i in range(self.dimension):
            byte_idx = i % len(hash_bytes)
            # Normalize to [-1, 1]
            value = (hash_bytes[byte_idx] / 127.5) - 1.0
            embedding.append(value)
        
        # Normalize vector
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [await self.embed(text) for text in texts]


class SemanticMemory:
    """
    Vector-based memory for semantic search.
    
    Stores documents with embeddings and provides:
    - Similarity search
    - Metadata filtering
    - Document clustering (future)
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        embedding_provider: Optional[EmbeddingProvider] = None,
        dimension: int = 384,
    ):
        """
        Initialize Semantic Memory.
        
        Args:
            event_bus: EventBus for publishing events.
            embedding_provider: Provider for generating embeddings.
            dimension: Embedding dimension.
        """
        self._event_bus = event_bus
        self._embedding_provider = embedding_provider or MockEmbeddingProvider(dimension)
        self._dimension = dimension
        
        # Storage: key -> (embedding, metadata, content)
        self._documents: Dict[str, Tuple[List[float], Dict[str, Any], str]] = {}
        
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_adds: int = 0
        self._total_searches: int = 0
        
        logger.info("SemanticMemory initialized (dimension=%d)", dimension)
    
    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a document to semantic memory.
        
        Args:
            doc_id: Unique document identifier.
            content: Document content.
            metadata: Optional metadata.
        """
        async with self._lock:
            self._total_adds += 1
            
            # Generate embedding
            embedding = await self._embedding_provider.embed(content)
            
            # Store
            self._documents[doc_id] = (embedding, metadata or {}, content)
            
            await self._event_bus.publish(Event(
                event_type="memory.semantic.added",
                payload={"doc_id": doc_id, "content_length": len(content)},
                timestamp=time.time(),
                source="semantic_memory",
            ))
            
            logger.debug("Added document '%s' to semantic memory", doc_id)
    
    async def add_documents_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> int:
        """
        Add multiple documents in batch.
        
        Args:
            documents: List of dicts with 'doc_id', 'content', and optional 'metadata'.
            
        Returns:
            Number of documents added.
        """
        async with self._lock:
            # Extract contents for batch embedding
            contents = [doc['content'] for doc in documents]
            embeddings = await self._embedding_provider.embed_batch(contents)
            
            # Store all
            for doc, embedding in zip(documents, embeddings):
                doc_id = doc['doc_id']
                self._documents[doc_id] = (
                    embedding,
                    doc.get('metadata', {}),
                    doc['content'],
                )
                self._total_adds += 1
            
            logger.info("Added %d documents in batch", len(documents))
            return len(documents)
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query.
            top_k: Number of results to return.
            min_score: Minimum similarity score.
            metadata_filter: Optional metadata filter.
            
        Returns:
            List of results with scores.
        """
        async with self._lock:
            self._total_searches += 1
            
            # Generate query embedding
            query_embedding = await self._embedding_provider.embed(query)
            
            # Calculate similarities
            results = []
            for doc_id, (embedding, metadata, content) in self._documents.items():
                # Apply metadata filter
                if metadata_filter:
                    if not self._matches_filter(metadata, metadata_filter):
                        continue
                
                # Calculate cosine similarity
                score = self._cosine_similarity(query_embedding, embedding)
                
                if score >= min_score:
                    results.append({
                        "doc_id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "score": score,
                    })
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document identifier.
            
        Returns:
            Document data, or None if not found.
        """
        if doc_id not in self._documents:
            return None
        
        embedding, metadata, content = self._documents[doc_id]
        return {
            "doc_id": doc_id,
            "content": content,
            "metadata": metadata,
        }
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: Document identifier.
            
        Returns:
            True if document was found and deleted.
        """
        async with self._lock:
            if doc_id in self._documents:
                del self._documents[doc_id]
                return True
            return False
    
    async def clear(self) -> int:
        """
        Clear all documents.
        
        Returns:
            Number of documents cleared.
        """
        async with self._lock:
            count = len(self._documents)
            self._documents.clear()
            logger.info("Cleared %d documents from semantic memory", count)
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get semantic memory statistics."""
        return {
            "total_documents": len(self._documents),
            "total_adds": self._total_adds,
            "total_searches": self._total_searches,
            "embedding_dimension": self._dimension,
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _matches_filter(
        self,
        metadata: Dict[str, Any],
        filter_dict: Dict[str, Any],
    ) -> bool:
        """Check if metadata matches filter."""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True
