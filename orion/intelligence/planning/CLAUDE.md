"""# CLAUDE.md - Planning Engine Subsystem

## 1. Overview
ORION's Planning Engine is the brain of the agent, responsible for translating high-level user goals into actionable, executable sequences of tasks. It leverages a Directed Acyclic Graph (DAG) to represent workflows, ensuring logical progression and dependency management.

## 2. Components
- **GoalManager (`goal_manager.py`):** Interprets user's natural language goals and converts them into structured internal representations.
- **PlanningEngine (`planning_engine.py`):** Generates a Task DAG from a structured goal, breaking it down into smaller, interdependent tasks.
- **TaskGraph (`task_graph.py`):** A data structure representing the DAG of tasks, including nodes (tasks) and edges (dependencies).

## 3. Interfaces (Contracts)
Planning-related data structures are defined in `orion/contracts/planning_contracts.py`.

### 3.1 GoalManager Interface
- `async parse_goal(natural_language_goal: str) -> StructuredGoal`: Converts a natural language goal into a structured format.

### 3.2 PlanningEngine Interface
- `async generate_task_dag(structured_goal: StructuredGoal) -> TaskGraph`: Generates a DAG of tasks from a structured goal.
- `async refine_task_dag(current_dag: TaskGraph, feedback: str) -> TaskGraph`: Refines an existing DAG based on feedback or new information.

## 4. Dependencies
- **Internal:** `orion.contracts.planning_contracts`, `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`, `orion.intelligence.clients.llm_client`
- **External:** `networkx` (for DAG representation), `asyncio`.

## 5. Build Order & Verification (Phase 3 - M3.1)
1. Define planning-related Pydantic models in `orion/contracts/planning_contracts.py`.
2. Implement `GoalManager` (initially with simple keyword parsing, later with LLM integration).
3. Implement `PlanningEngine` to create a basic DAG using `networkx`.
4. Create a demo script (`examples/planning_engine_demo.py`) to demonstrate goal parsing and DAG generation.
5. Ensure unit tests for `GoalManager` and `PlanningEngine` pass.
"""
