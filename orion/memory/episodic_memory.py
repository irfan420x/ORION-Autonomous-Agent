"""
ORION Episodic Memory
=====================

Experience logging and pattern recognition.

Features:
- Log actions, contexts, and outcomes
- Track success/failure patterns
- Extract lessons from experiences
- Find similar past episodes
- Learning from mistakes

Pattern: Observer pattern with event-driven logging
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.contracts.memory_contracts import Episode, MemoryType
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Experience logging and pattern recognition.
    
    Stores episodes (action-context-outcome tuples) and provides:
    - Pattern recognition from past experiences
    - Lesson extraction from failures
    - Similar episode search
    - Success rate tracking
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        max_episodes: int = 10000,
        db_path: str = "state/episodes.db",
    ):
        """
        Initialize Episodic Memory.
        
        Args:
            event_bus: EventBus for publishing events.
            max_episodes: Maximum episodes to store.
            db_path: Path to SQLite database for persistence.
        """
        self._event_bus = event_bus
        self._max_episodes = max_episodes
        self._db_path = db_path
        self._episodes: List[Episode] = []
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_logged: int = 0
        self._total_successes: int = 0
        self._total_failures: int = 0
        
        logger.info("EpisodicMemory initialized (max=%d)", max_episodes)
    
    async def log_episode(
        self,
        action: str,
        context: Dict[str, Any],
        outcome: str,
        success: bool,
        lessons_learned: Optional[List[str]] = None,
        related_memories: Optional[List[str]] = None,
    ) -> Episode:
        """
        Log a new episode.
        
        Args:
            action: What action was taken.
            context: Context when action was taken.
            outcome: Result of the action.
            success: Whether the action was successful.
            lessons_learned: Lessons from this episode.
            related_memories: Keys of related memories.
            
        Returns:
            The created episode.
        """
        async with self._lock:
            self._total_logged += 1
            if success:
                self._total_successes += 1
            else:
                self._total_failures += 1
            
            episode = Episode(
                episode_id=str(uuid.uuid4()),
                action=action,
                context=context,
                outcome=outcome,
                success=success,
                lessons_learned=lessons_learned or [],
                timestamp=time.time(),
                related_memories=related_memories or [],
            )
            
            self._episodes.append(episode)
            
            # Evict old episodes if at capacity
            while len(self._episodes) > self._max_episodes:
                self._episodes.pop(0)
            
            # Publish event
            await self._event_bus.publish(Event(
                event_type="memory.episodic.logged",
                payload={
                    "episode_id": episode.episode_id,
                    "action": action,
                    "success": success,
                },
                timestamp=episode.timestamp,
                source="episodic_memory",
            ))
            
            logger.debug("Logged episode: %s (success=%s)", action[:50], success)
            return episode
    
    async def get_similar_episodes(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 5,
    ) -> List[Episode]:
        """
        Find similar past episodes.
        
        Args:
            action: The action to find similar episodes for.
            context: Optional context to match.
            limit: Maximum results.
            
        Returns:
            List of similar episodes.
        """
        async with self._lock:
            scored_episodes = []
            
            for episode in self._episodes:
                score = self._calculate_similarity(episode, action, context)
                if score > 0.1:  # Minimum similarity threshold
                    scored_episodes.append((score, episode))
            
            # Sort by similarity score
            scored_episodes.sort(key=lambda x: x[0], reverse=True)
            
            return [ep for _, ep in scored_episodes[:limit]]
    
    async def get_lessons(self, action_pattern: Optional[str] = None) -> List[str]:
        """
        Get lessons learned from past episodes.
        
        Args:
            action_pattern: Optional pattern to filter actions.
            
        Returns:
            List of lessons.
        """
        async with self._lock:
            lessons = []
            
            for episode in self._episodes:
                if episode.lessons_learned:
                    if action_pattern is None or action_pattern.lower() in episode.action.lower():
                        lessons.extend(episode.lessons_learned)
            
            return list(set(lessons))  # Deduplicate
    
    async def get_success_rate(self, action_pattern: Optional[str] = None) -> float:
        """
        Calculate success rate for actions.
        
        Args:
            action_pattern: Optional pattern to filter actions.
            
        Returns:
            Success rate (0.0-1.0).
        """
        async with self._lock:
            matching = [
                ep for ep in self._episodes
                if action_pattern is None or action_pattern.lower() in ep.action.lower()
            ]
            
            if not matching:
                return 0.0
            
            successes = sum(1 for ep in matching if ep.success)
            return successes / len(matching)
    
    async def get_failure_patterns(self) -> List[Dict[str, Any]]:
        """
        Analyze failure patterns.
        
        Returns:
            List of failure patterns with frequency.
        """
        async with self._lock:
            failures = [ep for ep in self._episodes if not ep.success]
            
            # Group by action pattern
            pattern_counts: Dict[str, int] = {}
            for ep in failures:
                # Simple pattern extraction (first 50 chars of action)
                pattern = ep.action[:50]
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            # Sort by frequency
            patterns = [
                {"pattern": pattern, "count": count, "rate": count / len(failures) if failures else 0}
                for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
            ]
            
            return patterns[:10]
    
    async def get_episodes(
        self,
        limit: int = 100,
        success_only: Optional[bool] = None,
    ) -> List[Episode]:
        """
        Get recent episodes.
        
        Args:
            limit: Maximum results.
            success_only: If True, only successes. If False, only failures. If None, all.
            
        Returns:
            List of episodes.
        """
        async with self._lock:
            episodes = self._episodes
            
            if success_only is True:
                episodes = [ep for ep in episodes if ep.success]
            elif success_only is False:
                episodes = [ep for ep in episodes if not ep.success]
            
            return episodes[-limit:]
    
    async def clear(self) -> int:
        """
        Clear all episodes.
        
        Returns:
            Number of episodes cleared.
        """
        async with self._lock:
            count = len(self._episodes)
            self._episodes.clear()
            logger.info("Cleared %d episodes", count)
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get episodic memory statistics."""
        return {
            "total_episodes": len(self._episodes),
            "total_logged": self._total_logged,
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
            "success_rate": (
                self._total_successes / self._total_logged
                if self._total_logged > 0 else 0.0
            ),
        }
    
    def _calculate_similarity(
        self,
        episode: Episode,
        action: str,
        context: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate similarity between an episode and the given action/context."""
        score = 0.0
        
        # Action similarity (simple word overlap)
        action_words = set(action.lower().split())
        episode_words = set(episode.action.lower().split())
        
        if action_words and episode_words:
            overlap = len(action_words & episode_words)
            total = len(action_words | episode_words)
            score += (overlap / total) * 0.6
        
        # Context similarity (if provided)
        if context and episode.context:
            # Simple key overlap
            context_keys = set(context.keys())
            episode_keys = set(episode.context.keys())
            
            if context_keys and episode_keys:
                overlap = len(context_keys & episode_keys)
                total = len(context_keys | episode_keys)
                score += (overlap / total) * 0.4
        
        return score
