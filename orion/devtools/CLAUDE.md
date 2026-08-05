# CLAUDE.md - Developer Toolkit Subsystem

## 1. Overview
ORION's Developer Toolkit Subsystem provides advanced tools and interfaces for developers and power users to inspect, debug, and customize the agent's internal workings. It offers deep visibility into ORION's state, memory, task execution, and configuration, facilitating development and troubleshooting.

## 2. Components
- **DebugConsole (`debug_console.py`):** A real-time console for displaying logs, events, and agent states.
- **TaskViewer (`task_viewer.py`):** Visualizes the Task Graph (DAG) and Task Queue, showing task statuses and dependencies.
- **MemoryViewer (`memory_viewer.py`):** Provides an interactive view of ORION's multi-tiered memory architecture.
- **WorkflowEditor (`workflow_editor.py`):** A graphical interface for creating, editing, and visualizing workflows and skills.
- **PromptEditor (`prompt_editor.py`):** A tool for designing, testing, and optimizing LLM prompts.
- **EventViewer (`event_viewer.py`):** Displays a timeline of all events flowing through the Event Bus.
- **PluginManagerUI (`plugin_manager_ui.py`):** A GUI for managing installed plugins.
- **ConfigurationEditor (`config_editor.py`):** A user-friendly interface for editing ORION's YAML configuration files.

## 3. Interfaces (Contracts)
Developer toolkit-related data structures are defined in `orion/contracts/devtools_contracts.py`.

### 3.1 DebugConsole Interface
- `async display_log(log_entry: LogEntry)`: Displays a log entry in the console.
- `async execute_command(command: str) -> str`: Executes a debug command within the console.

### 3.2 TaskViewer Interface
- `async update_task_graph(task_graph: TaskGraph)`: Updates the visual representation of the task graph.
- `async highlight_task(task_id: str)`: Highlights a specific task in the viewer.

### 3.3 MemoryViewer Interface
- `async display_memory_state(memory_snapshot: Dict[str, Any])`: Displays a snapshot of the memory state.

## 4. Dependencies
- **Internal:** `orion.contracts.devtools_contracts`, `orion.contracts.agent_contracts`, `orion.contracts.planning_contracts`, `orion.contracts.observability_contracts`, `orion.core.communication.event_bus`, `orion.core.state.task_queue`, `orion.memory.session_memory`
- **External:** `asyncio`, `rich` (for console UI), `pygraphviz` (for graph visualization).

## 5. Build Order & Verification (Phase 7 - M7.5)
1. Define devtools-related Pydantic models in `orion/contracts/devtools_contracts.py`.
2. Implement `DebugConsole` for basic log display.
3. Implement `TaskViewer` (initially text-based, later graphical) to show task status.
4. Implement `MemoryViewer` to display session memory content.
5. Create a demo script (`examples/devtools_demo.py`) to demonstrate console output and task/memory inspection.
6. Ensure unit tests for all Developer Toolkit modules pass.
