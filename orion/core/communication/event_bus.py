"""
ORION Event Bus - Central Pub/Sub Communication System
=====================================================

The Event Bus is the sacred communication backbone of ORION.
All inter-agent and inter-module communication MUST go through this bus.

Key Features:
- Asynchronous pub/sub using Python asyncio
- Wildcard subscriptions (e.g., 'agent.*' matches 'agent.heartbeat')
- Thread-safe operations
- Event history for debugging (configurable)
- Graceful error handling (failed subscribers don't crash the bus)

Usage:
    bus = EventBus()
    await bus.subscribe("agent.heartbeat", my_handler)
    await bus.publish(Event(event_type="agent.heartbeat", payload={...}))
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Callable, Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

from orion.contracts.agent_contracts import Event

logger = logging.getLogger(__name__)


@dataclass
class SubscriberInfo:
    """Metadata about a subscriber."""
    callback: Callable
    event_pattern: str
    created_at: float = field(default_factory=time.time)
    call_count: int = 0
    last_error: Optional[str] = None


class EventBus:
    """
    Asynchronous Event Bus for ORION's inter-module communication.
    
    This is the central nervous system of ORION. All agents and modules
    communicate exclusively through this bus, ensuring loose coupling
    and scalability.
    
    Features:
    - Exact match subscriptions: "agent.heartbeat"
    - Wildcard subscriptions: "agent.*" matches all agent events
    - Global wildcard: "*" matches all events
    - Event history for debugging (configurable max size)
    - Subscriber error isolation (one failed handler doesn't affect others)
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize the Event Bus.
        
        Args:
            max_history: Maximum number of events to keep in history.
                        Set to 0 to disable history.
        """
        # Subscribers: event_pattern -> list of SubscriberInfo
        self._subscribers: Dict[str, List[SubscriberInfo]] = defaultdict(list)
        
        # Event history for debugging
        self._history: deque = deque(maxlen=max_history if max_history > 0 else 1)
        self._max_history = max_history
        
        # Statistics
        self._total_published: int = 0
        self._total_delivered: int = 0
        self._total_errors: int = 0
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("EventBus initialized (max_history=%d)", max_history)
    
    async def publish(self, event: Event) -> int:
        """
        Publish an event to all matching subscribers.
        
        Args:
            event: The Event to publish.
            
        Returns:
            Number of subscribers that received the event.
            
        Raises:
            ValueError: If event is invalid.
        """
        if not isinstance(event, Event):
            raise ValueError(f"Expected Event instance, got {type(event)}")
        
        async with self._lock:
            self._total_published += 1
            
            # Store in history
            if self._max_history > 0:
                self._history.append({
                    "event": event,
                    "published_at": time.time(),
                })
            
            # Find all matching subscribers
            matching_subscribers = self._find_matching_subscribers(event.event_type)
            
            if not matching_subscribers:
                logger.debug("No subscribers for event: %s", event.event_type)
                return 0
            
            # Deliver to all subscribers
            delivered = 0
            for subscriber_info in matching_subscribers:
                try:
                    # Call the subscriber
                    if asyncio.iscoroutinefunction(subscriber_info.callback):
                        await subscriber_info.callback(event)
                    else:
                        subscriber_info.callback(event)
                    
                    subscriber_info.call_count += 1
                    delivered += 1
                    self._total_delivered += 1
                    
                except Exception as e:
                    # Isolate errors - one failed subscriber doesn't affect others
                    self._total_errors += 1
                    subscriber_info.last_error = str(e)
                    logger.error(
                        "Subscriber error for %s: %s",
                        subscriber_info.event_pattern,
                        str(e),
                        exc_info=True
                    )
            
            logger.debug(
                "Published event '%s' to %d/%d subscribers",
                event.event_type,
                delivered,
                len(matching_subscribers)
            )
            
            return delivered
    
    async def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to events matching a pattern.
        
        Args:
            event_type: Event pattern to subscribe to.
                       - Exact: "agent.heartbeat"
                       - Wildcard: "agent.*" matches "agent.heartbeat", "agent.error", etc.
                       - Global: "*" matches all events
            callback: Async or sync function to call when event matches.
                     Signature: async def handler(event: Event) -> None
                     
        Raises:
            ValueError: If event_type is empty or callback is not callable.
        """
        if not event_type:
            raise ValueError("event_type cannot be empty")
        
        if not callable(callback):
            raise ValueError("callback must be callable")
        
        async with self._lock:
            subscriber_info = SubscriberInfo(
                callback=callback,
                event_pattern=event_type
            )
            self._subscribers[event_type].append(subscriber_info)
            
            logger.info("Subscribed to '%s'", event_type)
    
    async def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe a specific callback from an event type.
        
        Args:
            event_type: The event pattern to unsubscribe from.
            callback: The exact callback function to remove.
            
        Returns:
            True if the subscription was found and removed, False otherwise.
        """
        async with self._lock:
            if event_type not in self._subscribers:
                return False
            
            subscribers = self._subscribers[event_type]
            for i, sub_info in enumerate(subscribers):
                if sub_info.callback is callback:
                    subscribers.pop(i)
                    logger.info("Unsubscribed from '%s'", event_type)
                    return True
            
            return False
    
    async def unsubscribe_all(self, event_type: Optional[str] = None) -> int:
        """
        Remove all subscriptions, optionally for a specific event type.
        
        Args:
            event_type: If provided, only remove subscriptions for this pattern.
                       If None, remove ALL subscriptions.
                       
        Returns:
            Number of subscriptions removed.
        """
        async with self._lock:
            if event_type is not None:
                if event_type in self._subscribers:
                    count = len(self._subscribers[event_type])
                    del self._subscribers[event_type]
                    logger.info("Removed %d subscriptions for '%s'", count, event_type)
                    return count
                return 0
            else:
                total = sum(len(subs) for subs in self._subscribers.values())
                self._subscribers.clear()
                logger.info("Removed all %d subscriptions", total)
                return total
    
    def _find_matching_subscribers(self, event_type: str) -> List[SubscriberInfo]:
        """
        Find all subscribers whose pattern matches the given event type.
        
        Args:
            event_type: The event type to match against.
            
        Returns:
            List of matching SubscriberInfo objects.
        """
        matching = []
        
        for pattern, subscribers in self._subscribers.items():
            if self._pattern_matches(pattern, event_type):
                matching.extend(subscribers)
        
        return matching
    
    def _pattern_matches(self, pattern: str, event_type: str) -> bool:
        """
        Check if a subscription pattern matches an event type.
        
        Patterns:
        - "*": matches everything
        - "agent.*": matches "agent.heartbeat", "agent.error", etc.
        - "agent.heartbeat": exact match only
        """
        # Global wildcard
        if pattern == "*":
            return True
        
        # Wildcard pattern (e.g., "agent.*")
        if pattern.endswith(".*"):
            prefix = pattern[:-2]  # Remove ".*"
            return event_type.startswith(prefix + ".") or event_type == prefix
        
        # Exact match
        return pattern == event_type
    
    def get_subscribers(self, event_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about current subscribers.
        
        Args:
            event_type: If provided, only return subscribers for this pattern.
            
        Returns:
            Dictionary mapping event patterns to subscriber info.
        """
        result = {}
        
        patterns = [event_type] if event_type else self._subscribers.keys()
        
        for pattern in patterns:
            if pattern in self._subscribers:
                result[pattern] = [
                    {
                        "callback": sub.callback.__name__,
                        "created_at": sub.created_at,
                        "call_count": sub.call_count,
                        "last_error": sub.last_error,
                    }
                    for sub in self._subscribers[pattern]
                ]
        
        return result
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent event history.
        
        Args:
            limit: Maximum number of events to return.
            
        Returns:
            List of recent events with metadata.
        """
        history_list = list(self._history)
        return history_list[-limit:] if limit else history_list
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get EventBus statistics.
        
        Returns:
            Dictionary with statistics about the bus.
        """
        return {
            "total_published": self._total_published,
            "total_delivered": self._total_delivered,
            "total_errors": self._total_errors,
            "active_subscriptions": sum(len(subs) for subs in self._subscribers.values()),
            "unique_patterns": len(self._subscribers),
            "history_size": len(self._history),
        }
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._history.clear()
        logger.info("Event history cleared")
    
    async def wait_for_event(
        self,
        event_type: str,
        timeout: float = 30.0,
        filter_fn: Optional[Callable[[Event], bool]] = None
    ) -> Optional[Event]:
        """
        Wait for a specific event to occur.
        
        Args:
            event_type: The event type to wait for.
            timeout: Maximum time to wait in seconds.
            filter_fn: Optional function to filter events. Should return True for matching events.
            
        Returns:
            The matching Event, or None if timeout occurred.
        """
        result = None
        event_received = asyncio.Event()
        
        async def handler(event: Event):
            nonlocal result
            if filter_fn is None or filter_fn(event):
                result = event
                event_received.set()
        
        await self.subscribe(event_type, handler)
        
        try:
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for event '%s'", event_type)
        finally:
            await self.unsubscribe(event_type, handler)
        
        return result


# Global EventBus singleton (lazy initialization)
_global_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global EventBus singleton.
    
    Returns:
        The global EventBus instance.
    """
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


async def reset_event_bus() -> None:
    """
    Reset the global EventBus (useful for testing).
    
    WARNING: This will remove all subscriptions and history.
    """
    global _global_bus
    if _global_bus is not None:
        await _global_bus.unsubscribe_all()
        _global_bus.clear_history()
    _global_bus = None
