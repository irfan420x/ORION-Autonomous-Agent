# CLAUDE.md - World Model Subsystem

## 1. Overview
ORION's World Model Subsystem is responsible for building and maintaining a comprehensive, dynamic representation of the agent's operating environment. This includes the filesystem, running processes, network connections, Git repositories, and GUI windows. This model provides the agent with a crucial understanding of its surroundings, enabling informed decision-making and interaction.

## 2. Components
- **WorkspaceGraph (`workspace_graph.py`):** Represents the filesystem structure, including files, directories, and their relationships.
- **ProcessGraph (`process_graph.py`):** Maps running processes, their parent-child relationships, and resource usage.
- **NetworkGraph (`network_graph.py`):** Visualizes network connections, open ports, and active network interfaces.
- **FileGraph (`file_graph.py`):** Detailed view of individual files, their content, metadata, and access patterns.
- **GitGraph (`git_graph.py`):** Represents the state of Git repositories, including branches, commits, and changes.
- **WindowGraph (`window_graph.py`):** Maps open GUI windows, their titles, processes, and relationships.

## 3. Interfaces (Contracts)
World Model-related data structures and interfaces are defined in `orion/contracts/world_model_contracts.py`.

### 3.1 Graph Interfaces (Common)
- `async update_graph()`: Scans the environment and updates the graph.
- `async query_graph(query: str) -> Any`: Queries the graph for specific information.
- `async visualize_graph() -> str`: Generates a visual representation of the graph (e.g., DOT format, JSON for frontend).

## 4. Dependencies
- **Internal:** `orion.contracts.world_model_contracts`, `orion.core.communication.event_bus`, `orion.resource.resource_manager`
- **External:** `psutil`, `gitpython`, `pygetwindow` (or platform-specific window management libraries), `asyncio`.

## 5. Build Order & Verification (Phase 2 - M2.3)
1. Define graph-related Pydantic models in `orion/contracts/world_model_contracts.py`.
2. Implement `WorkspaceGraph` to scan and represent the filesystem.
3. Implement `ProcessGraph` to monitor running processes.
4. Implement `NetworkGraph` to detect network connections.
5. Implement `FileGraph` for detailed file information.
6. Implement `GitGraph` for Git repository status.
7. Implement `WindowGraph` for open GUI windows.
8. Create a demo script (`examples/world_model_demo.py`) to demonstrate updating and querying all graphs.
9. Ensure unit tests for all World Model modules pass.
