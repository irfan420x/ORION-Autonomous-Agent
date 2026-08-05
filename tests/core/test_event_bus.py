"""
Unit Tests for ORION Event Bus and Agent Registry
=================================================

Tests cover:
- EventBus: publish, subscribe, unsubscribe, wildcards, history, stats
- AgentRegistry: registration, deregistration, heartbeat, discovery
- Integration: EventBus + AgentRegistry working together
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from orion.contracts.agent_contracts import (
    AgentID,
    AgentCapability,
    AgentRegistration,
    AgentHeartbeat,
    Event,
)
from orion.core.communication.event_bus import EventBus, reset_event_bus
from orion.core.communication.registry import AgentRegistry


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def event_bus():
    """Create a fresh EventBus for each test."""
    return EventBus(max_history=100)


@pytest.fixture
def registry(event_bus):
    """Create a fresh AgentRegistry for each test."""
    return AgentRegistry(event_bus)


@pytest.fixture
def sample_event():
    """Create a sample event."""
    return Event(
        event_type="test.event",
        payload={"message": "hello"},
        timestamp=time.time(),
        source="test_agent",
    )


@pytest.fixture
def sample_registration():
    """Create a sample agent registration."""
    return AgentRegistration(
        agent_id="agent_001",
        capabilities=[
            AgentCapability(name="can_browse", version="1.0"),
            AgentCapability(name="can_code", version="1.0"),
        ],
        health_status="HEALTHY",
        endpoint="http://localhost:8001",
    )


@pytest.fixture
def sample_heartbeat():
    """Create a sample agent heartbeat."""
    return AgentHeartbeat(
        agent_id="agent_001",
        timestamp=time.time(),
        load_avg=[0.5, 0.3, 0.2],
        memory_usage_percent=45.0,
    )


# ============================================================================
# EventBus Tests
# ============================================================================

class TestEventBus:
    """Tests for the EventBus class."""
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, event_bus, sample_event):
        """Test basic subscribe and publish flow."""
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        await event_bus.subscribe("test.event", handler)
        delivered = await event_bus.publish(sample_event)
        
        assert delivered == 1
        assert len(received_events) == 1
        assert received_events[0].event_type == "test.event"
        assert received_events[0].payload == {"message": "hello"}
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus, sample_event):
        """Test that multiple subscribers receive the same event."""
        received_1 = []
        received_2 = []
        
        async def handler_1(event: Event):
            received_1.append(event)
        
        async def handler_2(event: Event):
            received_2.append(event)
        
        await event_bus.subscribe("test.event", handler_1)
        await event_bus.subscribe("test.event", handler_2)
        delivered = await event_bus.publish(sample_event)
        
        assert delivered == 2
        assert len(received_1) == 1
        assert len(received_2) == 1
    
    @pytest.mark.asyncio
    async def test_no_subscribers(self, event_bus, sample_event):
        """Test publishing to an event with no subscribers."""
        delivered = await event_bus.publish(sample_event)
        assert delivered == 0
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus, sample_event):
        """Test that unsubscribed handlers don't receive events."""
        received = []
        
        async def handler(event: Event):
            received.append(event)
        
        await event_bus.subscribe("test.event", handler)
        await event_bus.unsubscribe("test.event", handler)
        await event_bus.publish(sample_event)
        
        assert len(received) == 0
    
    @pytest.mark.asyncio
    async def test_wildcard_subscription(self, event_bus):
        """Test wildcard subscriptions (e.g., 'agent.*')."""
        received = []
        
        async def handler(event: Event):
            received.append(event)
        
        await event_bus.subscribe("agent.*", handler)
        
        # These should match
        event_1 = Event(event_type="agent.heartbeat", payload={}, timestamp=time.time(), source="a1")
        event_2 = Event(event_type="agent.error", payload={}, timestamp=time.time(), source="a1")
        
        # This should NOT match
        event_3 = Event(event_type="task.created", payload={}, timestamp=time.time(), source="t1")
        
        await event_bus.publish(event_1)
        await event_bus.publish(event_2)
        await event_bus.publish(event_3)
        
        assert len(received) == 2
        assert received[0].event_type == "agent.heartbeat"
        assert received[1].event_type == "agent.error"
    
    @pytest.mark.asyncio
    async def test_global_wildcard(self, event_bus):
        """Test global wildcard subscription ('*')."""
        received = []
        
        async def handler(event: Event):
            received.append(event)
        
        await event_bus.subscribe("*", handler)
        
        await event_bus.publish(Event(event_type="any.event", payload={}, timestamp=time.time(), source="s"))
        await event_bus.publish(Event(event_type="another.event", payload={}, timestamp=time.time(), source="s"))
        
        assert len(received) == 2
    
    @pytest.mark.asyncio
    async def test_sync_handler(self, event_bus, sample_event):
        """Test that sync (non-async) handlers work too."""
        received = []
        
        def handler(event: Event):
            received.append(event)
        
        await event_bus.subscribe("test.event", handler)
        await event_bus.publish(sample_event)
        
        assert len(received) == 1
    
    @pytest.mark.asyncio
    async def test_error_isolation(self, event_bus, sample_event):
        """Test that one failing handler doesn't affect others."""
        received_good = []
        
        async def bad_handler(event: Event):
            raise ValueError("Intentional error")
        
        async def good_handler(event: Event):
            received_good.append(event)
        
        await event_bus.subscribe("test.event", bad_handler)
        await event_bus.subscribe("test.event", good_handler)
        
        delivered = await event_bus.publish(sample_event)
        
        # Good handler should still receive the event
        assert len(received_good) == 1
        assert delivered == 1  # Only successful deliveries
    
    @pytest.mark.asyncio
    async def test_history(self, event_bus, sample_event):
        """Test event history recording."""
        await event_bus.publish(sample_event)
        await event_bus.publish(sample_event)
        
        history = event_bus.get_history(limit=10)
        assert len(history) == 2
        assert history[0]["event"].event_type == "test.event"
    
    @pytest.mark.asyncio
    async def test_stats(self, event_bus, sample_event):
        """Test statistics tracking."""
        async def handler(event: Event):
            pass
        
        await event_bus.subscribe("test.event", handler)
        await event_bus.publish(sample_event)
        await event_bus.publish(sample_event)
        
        stats = event_bus.get_stats()
        assert stats["total_published"] == 2
        assert stats["total_delivered"] == 2
        assert stats["active_subscriptions"] == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe_all(self, event_bus):
        """Test removing all subscriptions."""
        async def handler(event: Event):
            pass
        
        await event_bus.subscribe("event.1", handler)
        await event_bus.subscribe("event.2", handler)
        
        removed = await event_bus.unsubscribe_all()
        assert removed == 2
        
        stats = event_bus.get_stats()
        assert stats["active_subscriptions"] == 0
    
    @pytest.mark.asyncio
    async def test_wait_for_event(self, event_bus):
        """Test waiting for a specific event."""
        async def delayed_publish():
            await asyncio.sleep(0.1)
            event = Event(
                event_type="test.response",
                payload={"result": "ok"},
                timestamp=time.time(),
                source="test",
            )
            await event_bus.publish(event)
        
        # Start the delayed publisher
        asyncio.create_task(delayed_publish())
        
        # Wait for the event
        result = await event_bus.wait_for_event("test.response", timeout=2.0)
        
        assert result is not None
        assert result.payload["result"] == "ok"
    
    @pytest.mark.asyncio
    async def test_wait_for_event_timeout(self, event_bus):
        """Test that wait_for_event times out correctly."""
        result = await event_bus.wait_for_event("nonexistent.event", timeout=0.1)
        assert result is None


# ============================================================================
# AgentRegistry Tests
# ============================================================================

class TestAgentRegistry:
    """Tests for the AgentRegistry class."""
    
    @pytest.mark.asyncio
    async def test_register_agent(self, registry, sample_registration):
        """Test basic agent registration."""
        await registry.register_agent(sample_registration)
        
        agent = registry.get_agent("agent_001")
        assert agent is not None
        assert agent.agent_id == "agent_001"
        assert len(agent.capabilities) == 2
    
    @pytest.mark.asyncio
    async def test_register_duplicate_agent(self, registry, sample_registration):
        """Test that registering a duplicate agent raises ValueError."""
        await registry.register_agent(sample_registration)
        
        with pytest.raises(ValueError, match="already registered"):
            await registry.register_agent(sample_registration)
    
    @pytest.mark.asyncio
    async def test_deregister_agent(self, registry, sample_registration):
        """Test agent deregistration."""
        await registry.register_agent(sample_registration)
        
        result = await registry.deregister_agent("agent_001")
        assert result is True
        
        agent = registry.get_agent("agent_001")
        assert agent is None
    
    @pytest.mark.asyncio
    async def test_deregister_nonexistent_agent(self, registry):
        """Test deregistering an agent that doesn't exist."""
        result = await registry.deregister_agent("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_heartbeat(self, registry, sample_registration, sample_heartbeat):
        """Test heartbeat updates."""
        await registry.register_agent(sample_registration)
        await registry.update_agent_heartbeat(sample_heartbeat)
        
        info = registry.get_agent_info("agent_001")
        assert info is not None
        assert info["heartbeat_count"] == 1
    
    @pytest.mark.asyncio
    async def test_get_agents_by_capability(self, registry):
        """Test finding agents by capability."""
        reg_1 = AgentRegistration(
            agent_id="browser_agent",
            capabilities=[AgentCapability(name="can_browse", version="1.0")],
        )
        reg_2 = AgentRegistration(
            agent_id="code_agent",
            capabilities=[AgentCapability(name="can_code", version="1.0")],
        )
        reg_3 = AgentRegistration(
            agent_id="multi_agent",
            capabilities=[
                AgentCapability(name="can_browse", version="1.0"),
                AgentCapability(name="can_code", version="1.0"),
            ],
        )
        
        await registry.register_agent(reg_1)
        await registry.register_agent(reg_2)
        await registry.register_agent(reg_3)
        
        browse_agents = registry.get_agents_by_capability("can_browse")
        assert len(browse_agents) == 2
        
        code_agents = registry.get_agents_by_capability("can_code")
        assert len(code_agents) == 2
    
    @pytest.mark.asyncio
    async def test_get_healthy_agents(self, registry, sample_registration):
        """Test filtering for healthy agents."""
        await registry.register_agent(sample_registration)
        
        # Agent should be healthy immediately after registration
        healthy = registry.get_healthy_agents()
        assert len(healthy) == 1
    
    @pytest.mark.asyncio
    async def test_get_stale_agents(self, registry, sample_registration):
        """Test detecting stale agents."""
        await registry.register_agent(sample_registration)
        
        # Simulate stale agent by setting last_heartbeat to past
        agent_info = registry._agents["agent_001"]
        agent_info.last_heartbeat = time.time() - 60  # 60 seconds ago
        
        stale = registry.get_stale_agents()
        assert len(stale) == 1
        assert stale[0].agent_id == "agent_001"
    
    @pytest.mark.asyncio
    async def test_capabilities_index(self, registry):
        """Test capabilities index building."""
        reg = AgentRegistration(
            agent_id="agent_001",
            capabilities=[
                AgentCapability(name="can_browse", version="1.0"),
                AgentCapability(name="can_code", version="1.0"),
            ],
        )
        
        await registry.register_agent(reg)
        
        index = registry.get_capabilities_index()
        assert "can_browse" in index
        assert "can_code" in index
        assert "agent_001" in index["can_browse"]
    
    @pytest.mark.asyncio
    async def test_stats(self, registry, sample_registration, sample_heartbeat):
        """Test statistics tracking."""
        await registry.register_agent(sample_registration)
        await registry.update_agent_heartbeat(sample_heartbeat)
        
        stats = registry.get_stats()
        assert stats["total_agents"] == 1
        assert stats["total_registrations"] == 1
        assert stats["total_heartbeats"] == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Tests for EventBus + AgentRegistry working together."""
    
    @pytest.mark.asyncio
    async def test_registration_publishes_event(self, event_bus, registry, sample_registration):
        """Test that registering an agent publishes an event to the bus."""
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        await event_bus.subscribe("agent.registered", handler)
        await registry.register_agent(sample_registration)
        
        assert len(received_events) == 1
        assert received_events[0].payload["agent_id"] == "agent_001"
    
    @pytest.mark.asyncio
    async def test_deregistration_publishes_event(self, event_bus, registry, sample_registration):
        """Test that deregistering an agent publishes an event to the bus."""
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        await registry.register_agent(sample_registration)
        await event_bus.subscribe("agent.deregistered", handler)
        await registry.deregister_agent("agent_001")
        
        assert len(received_events) == 1
        assert received_events[0].payload["agent_id"] == "agent_001"
    
    @pytest.mark.asyncio
    async def test_heartbeat_via_event_bus(self, event_bus, registry, sample_registration):
        """Test that heartbeats received via EventBus update the registry."""
        await registry.register_agent(sample_registration)
        await registry.start()
        
        # Publish a heartbeat event
        heartbeat_event = Event(
            event_type="agent.heartbeat",
            payload={
                "agent_id": "agent_001",
                "timestamp": time.time(),
                "load_avg": [0.5, 0.3, 0.2],
                "memory_usage_percent": 50.0,
            },
            timestamp=time.time(),
            source="agent_001",
        )
        
        await event_bus.publish(heartbeat_event)
        
        info = registry.get_agent_info("agent_001")
        assert info["heartbeat_count"] == 1
        
        await registry.stop()


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests to ensure the EventBus can handle high throughput."""
    
    @pytest.mark.asyncio
    async def test_throughput_1000_messages(self, event_bus):
        """Test that EventBus can handle 1000 messages/sec."""
        received_count = 0
        
        async def handler(event: Event):
            nonlocal received_count
            received_count += 1
        
        await event_bus.subscribe("perf.test", handler)
        
        # Publish 1000 events
        start_time = time.time()
        for i in range(1000):
            event = Event(
                event_type="perf.test",
                payload={"index": i},
                timestamp=time.time(),
                source="perf_test",
            )
            await event_bus.publish(event)
        elapsed = time.time() - start_time
        
        assert received_count == 1000
        # Should complete in under 1 second
        assert elapsed < 1.0, f"Throughput test took {elapsed:.2f}s (expected < 1.0s)"
    
    @pytest.mark.asyncio
    async def test_concurrent_publishers(self, event_bus):
        """Test concurrent publishing from multiple sources."""
        received_count = 0
        
        async def handler(event: Event):
            nonlocal received_count
            received_count += 1
        
        await event_bus.subscribe("concurrent.test", handler)
        
        async def publisher(source_id: int, count: int):
            for i in range(count):
                event = Event(
                    event_type="concurrent.test",
                    payload={"source": source_id, "index": i},
                    timestamp=time.time(),
                    source=f"source_{source_id}",
                )
                await event_bus.publish(event)
        
        # Run 10 concurrent publishers, each sending 100 events
        tasks = [publisher(i, 100) for i in range(10)]
        await asyncio.gather(*tasks)
        
        assert received_count == 1000
