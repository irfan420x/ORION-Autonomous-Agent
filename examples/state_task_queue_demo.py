"""
State Machine & Task Queue Demo
================================
Demonstrates ORION's StateMachine and TaskQueueEngine.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from orion.core.state.state_machine import StateMachine, State
from orion.core.state.task_queue import TaskQueueEngine
from orion.core.communication.event_bus import EventBus
from orion.contracts.agent_contracts import Task, TaskID, TaskStatus

async def main():
    print("--- State Machine & Task Queue Demo Start ---")

    # Initialize EventBus (required by StateMachine and TaskQueueEngine)
    event_bus = EventBus()
    state_machine = StateMachine(event_bus)
    print(f"Initial State: {state_machine.current_state}")

    await state_machine.transition_to(State.PROCESSING)
    print(f"Current State: {state_machine.current_state}")

    # Initialize Task Queue Engine
    os.makedirs("state", exist_ok=True)
    task_queue_engine = TaskQueueEngine(event_bus, "state/task_queue_demo.json")
    await task_queue_engine.load_state()

    # Create some tasks
    now = time.time()
    task1 = Task(task_id=TaskID("task_001"), goal="Analyze sales data", created_at=now, updated_at=now)
    task2 = Task(task_id=TaskID("task_002"), goal="Generate report", dependencies=[TaskID("task_001")], created_at=now, updated_at=now)
    task3 = Task(task_id=TaskID("task_003"), goal="Deploy model", created_at=now, updated_at=now)

    await task_queue_engine.add_task(task1)
    await task_queue_engine.add_task(task2)
    await task_queue_engine.add_task(task3)

    print("\n--- Tasks in Queue ---")
    tasks = await task_queue_engine.get_all_tasks()
    for task in tasks:
        print(f"  Task ID: {task.task_id}, Goal: {task.goal}, Status: {task.status}, Dependencies: {task.dependencies}")

    # Get next task (should be task1 as it has no dependencies)
    next_task = await task_queue_engine.get_next_task()
    if next_task:
        print(f"\nNext task to execute: {next_task.task_id} - {next_task.goal}")
        await task_queue_engine.update_task_status(str(next_task.task_id), "EXECUTING")
        print(f"Updated status of {next_task.task_id} to EXECUTING")

    # Try to get next task again (should be task3 as task2 depends on task1)
    next_task = await task_queue_engine.get_next_task()
    if next_task:
        print(f"Next task to execute: {next_task.task_id} - {next_task.goal}")
        await task_queue_engine.update_task_status(str(next_task.task_id), "EXECUTING")

    # Simulate task1 completion
    await task_queue_engine.update_task_status("task_001", "COMPLETED")
    print(f"\nSimulated completion of task_001")

    # Now task2 should be available
    next_task = await task_queue_engine.get_next_task()
    if next_task:
        print(f"Next task to execute: {next_task.task_id} - {next_task.goal}")

    await task_queue_engine.persist_state()
    print("\nTask queue state persisted.")

    print("\n--- Final State of Tasks ---")
    tasks = await task_queue_engine.get_all_tasks()
    for task in tasks:
        print(f"  Task ID: {task.task_id}, Goal: {task.goal}, Status: {task.status}")

    print("\n--- State Machine Stats ---")
    stats = state_machine.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n--- Task Queue Stats ---")
    tq_stats = task_queue_engine.get_stats()
    for k, v in tq_stats.items():
        print(f"  {k}: {v}")

    # Cleanup demo state file
    if os.path.exists("state/task_queue_demo.json"):
        os.remove("state/task_queue_demo.json")

    print("\n--- State Machine & Task Queue Demo End ---")

if __name__ == "__main__":
    asyncio.run(main())
