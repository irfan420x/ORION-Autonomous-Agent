import asyncio
import time
from orion.core.communication.event_bus import EventBus
from orion.contracts.agent_contracts import Event, AgentID, AgentRegistration, AgentCapability, AgentHeartbeat

class MockAgent:
    def __init__(self, agent_id: str, capabilities: list[str], event_bus: EventBus):
        self.agent_id = AgentID(agent_id)
        self.capabilities = [AgentCapability(name=cap) for cap in capabilities]
        self.event_bus = event_bus
        self.received_events = []

    async def register(self):
        registration = AgentRegistration(
            agent_id=self.agent_id,
            capabilities=self.capabilities,
            health_status="HEALTHY",
            endpoint=f"http://localhost:8000/{self.agent_id}"
        )
        # In a real scenario, AgentRegistry would handle this, but for demo, we mock it.
        print(f"[{self.agent_id}] Registering with capabilities: {[c.name for c in self.capabilities]}")

    async def handle_event(self, event: Event):
        print(f"[{self.agent_id}] Received event: {event.event_type} from {event.source} with payload {event.payload}")
        self.received_events.append(event)

    async def send_heartbeat(self):
        heartbeat = AgentHeartbeat(
            agent_id=self.agent_id,
            timestamp=time.time(),
            load_avg=[0.1, 0.2, 0.3],
            memory_usage_percent=25.5
        )
        await self.event_bus.publish(Event(
            event_type="agent.heartbeat",
            payload=heartbeat.model_dump(),
            timestamp=time.time(),
            source=self.agent_id
        ))

async def main():
    print("--- Event Bus Demo Start ---")
    event_bus = EventBus()

    # Mock AgentRegistry for demo purposes
    registered_agents = {}
    async def mock_register_agent(event: Event):
        reg_data = AgentRegistration(**event.payload)
        registered_agents[reg_data.agent_id] = reg_data
        print(f"[MockRegistry] Agent {reg_data.agent_id} registered.")
    await event_bus.subscribe("agent.register", mock_register_agent)

    # Create mock agents
    agent_a = MockAgent("AgentA", ["can_browse", "can_code"], event_bus)
    agent_b = MockAgent("AgentB", ["can_analyze"], event_bus)
    agent_c = MockAgent("AgentC", ["can_code"], event_bus)

    # Agents register themselves (mocked via event)
    await event_bus.publish(Event(
        event_type="agent.register",
        payload=AgentRegistration(agent_id=agent_a.agent_id, capabilities=agent_a.capabilities, health_status="HEALTHY").model_dump(),
        timestamp=time.time(),
        source=agent_a.agent_id
    ))
    await event_bus.publish(Event(
        event_type="agent.register",
        payload=AgentRegistration(agent_id=agent_b.agent_id, capabilities=agent_b.capabilities, health_status="HEALTHY").model_dump(),
        timestamp=time.time(),
        source=agent_b.agent_id
    ))

    # Agents subscribe to events
    await event_bus.subscribe("task.new", agent_a.handle_event)
    await event_bus.subscribe("task.new", agent_b.handle_event)
    await event_bus.subscribe("agent.heartbeat", agent_c.handle_event) # AgentC monitors heartbeats

    # Agent A sends a heartbeat
    await agent_a.send_heartbeat()

    # Orchestrator publishes a new task
    new_task_event = Event(
        event_type="task.new",
        payload={"task_id": "task_123", "description": "Analyze sales data"},
        timestamp=time.time(),
        source=AgentID("Orchestrator")
    )
    await event_bus.publish(new_task_event)

    # Give some time for async tasks to process
    await asyncio.sleep(0.1)

    print("\n--- Registered Agents (Mock) ---")
    for agent_id, reg_data in registered_agents.items():
        print(f"ID: {agent_id}, Capabilities: {[c.name for c in reg_data.capabilities]}")

    print("\n--- Agent A received events ---")
    for event in agent_a.received_events:
        print(f"  {event.event_type} from {event.source}")

    print("\n--- Agent B received events ---")
    for event in agent_b.received_events:
        print(f"  {event.event_type} from {event.source}")

    print("\n--- Agent C received events ---")
    for event in agent_c.received_events:
        print(f"  {event.event_type} from {event.source}")

    print("--- Event Bus Demo End ---")

if __name__ == "__main__":
    # This will fail until EventBus.publish and subscribe are implemented
    try:
        asyncio.run(main())
    except NotImplementedError as e:
        print(f"\nERROR: {e}. Please implement EventBus.publish and EventBus.subscribe first.")

