# CLAUDE.md - Core Communication Subsystem

## 1. Overview
This subsystem is responsible for all inter-agent and inter-module communication within ORION. It is built around a central, asynchronous Event Bus, ensuring loose coupling and scalability.

## 2. Components
- **EventBus (`event_bus.py`):** The central Pub/Sub mechanism for all internal events.
- **AgentRegistry (`registry.py`):** Manages the registration, capabilities, and health status of all active agents.
- **AgentHeartbeat:** Mechanism for agents to periodically report their liveness and status.

## 3. Interfaces (Contracts)
All communication events and agent metadata are defined in `orion/contracts/agent_contracts.py` using Pydantic models.

### 3.1 EventBus Interface
- `async publish(event: Event)`: Publishes an event to all subscribed listeners.
- `async subscribe(event_type: str, callback: Callable)`: Registers a callback function to receive events of a specific type.

### 3.2 AgentRegistry Interface
- `async register_agent(registration: AgentRegistration)`: Registers a new agent with its capabilities.
- `async update_agent_heartbeat(heartbeat: AgentHeartbeat)`: Updates an agent's liveness status.
- `async get_agent_capabilities(agent_id: AgentID) -> List[AgentCapability]`: Retrieves capabilities of a registered agent.

## 4. Dependencies
- **Internal:** `orion.contracts.agent_contracts`
- **External:** `asyncio` (for EventBus implementation)

## 5. Build Order & Verification (Phase 1 - M1.1)
1. Implement `EventBus` (publish/subscribe methods).
2. Implement `AgentRegistry` (register/update/get methods).
3. Create a simple demo script (`examples/event_bus_demo.py`) to verify basic pub/sub and agent registration.
4. Ensure unit tests for `event_bus.py` and `registry.py` pass.
