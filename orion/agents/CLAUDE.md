"""# CLAUDE.md - Agent System

## 1. Overview
ORION's Agent System is the core of its multi-agent architecture. It defines the base structure for all agents and manages their lifecycle, communication, and execution within the ORION ecosystem. Each agent is designed to be specialized, focusing on a particular set of capabilities or tasks.

## 2. Components
- **BaseAgent (`base_agent.py`):** Provides the foundational structure and common functionalities for all agents, including registration, heartbeat, and event handling.
- **OrchestratorAgent (`orchestrator_agent.py`):** The high-level agent responsible for interpreting user goals, initiating planning, and overseeing the execution of tasks across other agents.
- **PlannerAgent (`planner_agent.py`):** Interacts with the Planning Engine to generate and refine task DAGs.
- **ExecutorAgent (`executor_agent.py`):** Responsible for executing individual tasks within a workflow, coordinating with specialized agents or tools.
- **Specialized Agents (e.g., BrowserAgent, VisionAgent, CodeAgent):** Agents designed to handle specific domains or interact with particular external systems.

## 3. Interfaces (Contracts)
Agent-related data structures and interfaces are defined in `orion/contracts/agent_contracts.py`.

### 3.1 BaseAgent Interface
- `async start()`: Initializes the agent, registers it with the Event Bus, and starts its main loop.
- `async stop()`: Gracefully shuts down the agent.
- `async handle_event(event: Event)`: Processes incoming events from the Event Bus.
- `async execute_task(task: Task)`: Executes a given task (abstract method, implemented by specialized agents).

## 4. Dependencies
- **Internal:** `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`, `orion.core.state.state_machine`, `orion.core.state.task_queue`, `orion.intelligence.planning.planning_engine`
- **External:** `asyncio`.

## 5. Build Order & Verification (Phase 4 - M4.1)
1. Ensure `agent_contracts.py` is complete with `AgentID`, `AgentRegistration`, `Event`, `Task` definitions.
2. Implement `BaseAgent` with basic event subscription and heartbeat publishing.
3. Implement `OrchestratorAgent` to initiate a simple planning process and assign tasks.
4. Implement `PlannerAgent` to interact with a mocked `PlanningEngine`.
5. Implement `ExecutorAgent` to simulate task execution.
6. Create a demo script (`examples/multi_agent_demo.py`) to demonstrate agents registering, communicating, and executing a simple task.
7. Ensure unit tests for `BaseAgent`, `OrchestratorAgent`, `PlannerAgent`, and `ExecutorAgent` pass.
"""
