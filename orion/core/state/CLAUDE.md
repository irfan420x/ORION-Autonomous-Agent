# CLAUDE.md - Core State Management Subsystem

## 1. Overview
This subsystem is responsible for managing the overall state of the ORION agent, including its current operational state, active tasks, and the lifecycle of workflows. It ensures that ORION can maintain its operational context across sessions and recover gracefully from interruptions.

## 2. Components
- **StateMachine (`state_machine.py`):** Manages the agent's operational states (e.g., IDLE, PLANNING, EXECUTING, PAUSED, RECOVERING) and transitions between them.
- **TaskQueueEngine (`task_queue.py`):** Manages the queue of tasks to be executed, including task prioritization, dependency resolution, and persistence.

## 3. Interfaces (Contracts)
All task-related data structures are defined in `orion/contracts/agent_contracts.py` using Pydantic models.

### 3.1 StateMachine Interface
- `async transition_to(new_state: str)`: Changes the agent's current operational state.
- `async get_current_state() -> str`: Retrieves the current operational state.

### 3.2 TaskQueueEngine Interface
- `async add_task(task: Task)`: Adds a new task to the queue.
- `async get_next_task() -> Optional[Task]`: Retrieves the next task to be executed based on priority and dependencies.
- `async update_task_status(task_id: TaskID, status: TaskStatus)`: Updates the status of a specific task.
- `async persist_state()`: Saves the current task queue state to `state/task_queue.json`.
- `async load_state()`: Loads the task queue state from `state/task_queue.json`.

## 4. Dependencies
- **Internal:** `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`
- **External:** `asyncio`, `json` (for persistence)

## 5. Build Order & Verification (Phase 1 - M1.2)
1. Implement `StateMachine` with basic state transitions.
2. Implement `TaskQueueEngine` with add, get, update, persist, and load functionalities.
3. Create a simple demo script (`examples/state_task_queue_demo.py`) to verify state transitions and task management.
4. Ensure unit tests for `state_machine.py` and `task_queue.py` pass.
