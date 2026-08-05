"""
ORION Agent Registry - Agent Discovery & Management
===================================================

The Agent Registry manages the registration, capabilities, and health
status of all active agents in the ORION system.

Key Features:
- Agent registration with capabilities
- Heartbeat monitoring
- Agent discovery by capability
- Health status tracking

Usage:
    registry = AgentRegistry(event_bus)
    await registry.register_agent(registration)
    agents = registry.get_agents_by_capability("can_browse")
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

from orion.contracts.agent_contracts import (
    AgentID,
    AgentCapability,
    AgentRegistration,
    AgentHeartbeat,
    Event,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentInfo:
    """Internal representation of a registered agent."""
    registration: AgentRegistration
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    heartbeat_count: int = 0
    capabilities_index: Set[str] = field(default_factory=set)


class AgentRegistry:
    """
    Manages agent registration, discovery, and health monitoring.
    
    The Registry works closely with the EventBus to:
    - Publish 'agent.registered' events when new agents join
    - Publish 'agent.deregistered' events when agents leave
    - Listen for 'agent.heartbeat' events to track liveness
    - Provide agent discovery by capability
    """
    
    # How long before an agent is considered stale (no heartbeat)
    STALE_THRESHOLD_SECONDS: float = 30.0
    
    def __init__(self, event_bus: Any):
        """
        Initialize the Agent Registry.
        
        Args:
            event_bus: The EventBus instance for publishing/listening to events.
        """
        self._event_bus = event_bus
        self._agents: Dict[AgentID, AgentInfo] = {}
        self._lock = asyncio.Lock()
        
        # Statistics
        self._total_registrations: int = 0
        self._total_deregistrations: int = 0
        self._total_heartbeats: int = 0
        
        logger.info("AgentRegistry initialized")
    
    async def start(self) -> None:
        """
        Start the registry by subscribing to heartbeat events.
        
        Call this after the EventBus is fully initialized.
        """
        await self._event_bus.subscribe("agent.heartbeat", self._handle_heartbeat)
        logger.info("AgentRegistry started, listening for heartbeats")
    
    async def stop(self) -> None:
        """Stop the registry and unsubscribe from events."""
        await self._event_bus.unsubscribe("agent.heartbeat", self._handle_heartbeat)
        logger.info("AgentRegistry stopped")
    
    async def register_agent(self, registration: AgentRegistration) -> None:
        """
        Register a new agent with its capabilities.
        
        Args:
            registration: The agent's registration data.
            
        Raises:
            ValueError: If agent_id is empty or already registered.
        """
        if not registration.agent_id:
            raise ValueError("agent_id cannot be empty")
        
        async with self._lock:
            if registration.agent_id in self._agents:
                raise ValueError(f"Agent '{registration.agent_id}' is already registered")
            
            # Create AgentInfo with indexed capabilities
            capabilities_index = {cap.name for cap in registration.capabilities}
            
            agent_info = AgentInfo(
                registration=registration,
                capabilities_index=capabilities_index,
            )
            
            self._agents[registration.agent_id] = agent_info
            self._total_registrations += 1
            
            # Publish registration event
            await self._event_bus.publish(Event(
                event_type="agent.registered",
                payload={
                    "agent_id": registration.agent_id,
                    "capabilities": [cap.name for cap in registration.capabilities],
                    "health_status": registration.health_status,
                },
                timestamp=time.time(),
                source=registration.agent_id,
            ))
            
            logger.info(
                "Agent '%s' registered with capabilities: %s",
                registration.agent_id,
                [cap.name for cap in registration.capabilities]
            )
    
    async def deregister_agent(self, agent_id: AgentID) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: The ID of the agent to remove.
            
        Returns:
            True if the agent was found and removed, False otherwise.
        """
        async with self._lock:
            if agent_id not in self._agents:
                return False
            
            del self._agents[agent_id]
            self._total_deregistrations += 1
            
            # Publish deregistration event
            await self._event_bus.publish(Event(
                event_type="agent.deregistered",
                payload={"agent_id": agent_id},
                timestamp=time.time(),
                source=agent_id,
            ))
            
            logger.info("Agent '%s' deregistered", agent_id)
            return True
    
    async def update_agent_heartbeat(self, heartbeat: AgentHeartbeat) -> None:
        """
        Update an agent's heartbeat status.
        
        Args:
            heartbeat: The heartbeat data from the agent.
        """
        async with self._lock:
            if heartbeat.agent_id not in self._agents:
                logger.warning(
                    "Received heartbeat from unknown agent '%s'",
                    heartbeat.agent_id
                )
                return
            
            agent_info = self._agents[heartbeat.agent_id]
            agent_info.last_heartbeat = heartbeat.timestamp
            agent_info.heartbeat_count += 1
            self._total_heartbeats += 1
            
            logger.debug(
                "Heartbeat from '%s' (count: %d)",
                heartbeat.agent_id,
                agent_info.heartbeat_count
            )
    
    async def _handle_heartbeat(self, event: Event) -> None:
        """
        Handle incoming heartbeat events from the EventBus.
        
        Args:
            event: The heartbeat event.
        """
        try:
            heartbeat = AgentHeartbeat(**event.payload)
            await self.update_agent_heartbeat(heartbeat)
        except Exception as e:
            logger.error("Failed to process heartbeat event: %s", str(e))
    
    def get_agent(self, agent_id: AgentID) -> Optional[AgentRegistration]:
        """
        Get registration data for a specific agent.
        
        Args:
            agent_id: The ID of the agent to look up.
            
        Returns:
            The agent's registration, or None if not found.
        """
        agent_info = self._agents.get(agent_id)
        return agent_info.registration if agent_info else None
    
    def get_all_agents(self) -> List[AgentRegistration]:
        """
        Get registration data for all registered agents.
        
        Returns:
            List of all agent registrations.
        """
        return [info.registration for info in self._agents.values()]
    
    def get_agents_by_capability(self, capability_name: str) -> List[AgentRegistration]:
        """
        Find all agents that have a specific capability.
        
        Args:
            capability_name: The capability to search for.
            
        Returns:
            List of agents with the specified capability.
        """
        return [
            info.registration
            for info in self._agents.values()
            if capability_name in info.capabilities_index
        ]
    
    def get_healthy_agents(self) -> List[AgentRegistration]:
        """
        Get all agents that are currently healthy.
        
        An agent is considered healthy if:
        1. Its health_status is "HEALTHY"
        2. It has sent a heartbeat within STALE_THRESHOLD_SECONDS
        
        Returns:
            List of healthy agent registrations.
        """
        now = time.time()
        healthy = []
        
        for info in self._agents.values():
            # Check health status
            if info.registration.health_status != "HEALTHY":
                continue
            
            # Check heartbeat freshness
            time_since_heartbeat = now - info.last_heartbeat
            if time_since_heartbeat <= self.STALE_THRESHOLD_SECONDS:
                healthy.append(info.registration)
        
        return healthy
    
    def get_stale_agents(self) -> List[AgentRegistration]:
        """
        Get all agents that haven't sent a heartbeat recently.
        
        Returns:
            List of stale agent registrations.
        """
        now = time.time()
        stale = []
        
        for info in self._agents.values():
            time_since_heartbeat = now - info.last_heartbeat
            if time_since_heartbeat > self.STALE_THRESHOLD_SECONDS:
                stale.append(info.registration)
        
        return stale
    
    def get_capabilities_index(self) -> Dict[str, List[AgentID]]:
        """
        Build an index of capabilities to agents.
        
        Returns:
            Dictionary mapping capability names to lists of agent IDs.
        """
        index: Dict[str, List[AgentID]] = {}
        
        for info in self._agents.values():
            for cap_name in info.capabilities_index:
                if cap_name not in index:
                    index[cap_name] = []
                index[cap_name].append(info.registration.agent_id)
        
        return index
    
    def get_agent_info(self, agent_id: AgentID) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an agent.
        
        Args:
            agent_id: The ID of the agent.
            
        Returns:
            Dictionary with agent details, or None if not found.
        """
        if agent_id not in self._agents:
            return None
        
        info = self._agents[agent_id]
        now = time.time()
        
        return {
            "agent_id": info.registration.agent_id,
            "capabilities": [cap.name for cap in info.registration.capabilities],
            "health_status": info.registration.health_status,
            "endpoint": info.registration.endpoint,
            "registered_at": info.registered_at,
            "last_heartbeat": info.last_heartbeat,
            "heartbeat_count": info.heartbeat_count,
            "time_since_heartbeat": now - info.last_heartbeat,
            "is_stale": (now - info.last_heartbeat) > self.STALE_THRESHOLD_SECONDS,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with statistics about the registry.
        """
        now = time.time()
        
        # Count stale agents
        stale_count = sum(
            1 for info in self._agents.values()
            if (now - info.last_heartbeat) > self.STALE_THRESHOLD_SECONDS
        )
        
        return {
            "total_agents": len(self._agents),
            "healthy_agents": len(self._agents) - stale_count,
            "stale_agents": stale_count,
            "total_registrations": self._total_registrations,
            "total_deregistrations": self._total_deregistrations,
            "total_heartbeats": self._total_heartbeats,
            "unique_capabilities": len(self.get_capabilities_index()),
        }
