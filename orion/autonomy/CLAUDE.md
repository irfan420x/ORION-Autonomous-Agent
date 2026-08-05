"""# CLAUDE.md - Autonomy Subsystem

## 1. Overview
ORION's Autonomy Subsystem empowers the agent to perform tasks proactively and independently, without constant human intervention. It includes mechanisms for scheduling tasks, monitoring the environment for triggers, and generating reports on its autonomous activities.

## 2. Components
- **Scheduler (`scheduler.py`):** Manages and executes tasks at predefined times or intervals (e.g., cron-like functionality).
- **Watcher (`watcher.py`):** Monitors specific events or changes in the environment (e.g., file changes, system metrics thresholds) and triggers appropriate actions.
- **AutoReporter (`auto_reporter.py`):** Generates periodic or event-driven reports on ORION's activities, system status, or task outcomes.

## 3. Interfaces (Contracts)
Autonomy-related data structures are defined in `orion/contracts/autonomy_contracts.py`.

### 3.1 Scheduler Interface
- `async schedule_task(task: Task, schedule: ScheduleDefinition)`: Schedules a task for future execution.
- `async cancel_scheduled_task(task_id: str)`: Cancels a previously scheduled task.

### 3.2 Watcher Interface
- `async create_watcher(watcher_config: WatcherConfig)`: Creates and activates a new watcher.
- `async disable_watcher(watcher_id: str)`: Disables an active watcher.

### 3.3 AutoReporter Interface
- `async generate_report(report_type: str, period: Optional[str] = None) -> Report`: Generates a report of a specified type and period.

## 4. Dependencies
- **Internal:** `orion.contracts.autonomy_contracts`, `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`, `orion.core.state.task_queue`, `orion.world_model.file_graph`, `orion.resource.resource_manager`
- **External:** `asyncio`, `apscheduler` (for scheduling), `watchdog` (for file system watching).

## 5. Build Order & Verification (Phase 7 - M7.1)
1. Define autonomy-related Pydantic models in `orion/contracts/autonomy_contracts.py`.
2. Implement `Scheduler` with basic cron-like scheduling.
3. Implement `Watcher` for file system event monitoring.
4. Implement `AutoReporter` for generating simple text reports.
5. Create a demo script (`examples/autonomy_demo.py`) to demonstrate scheduling a task and triggering an action based on a file change.
6. Ensure unit tests for all Autonomy modules pass.
"""
