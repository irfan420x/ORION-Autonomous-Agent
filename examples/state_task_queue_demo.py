import asyncio
import time
import os
from orion.core.state.state_machine import StateMachine
from orion.core.state.task_queue import TaskQueueEngine
from orion.contracts.agent_contracts import Task, TaskID, TaskStatus

async def main():
    print("--- State Machine & Task Queue Demo Start ---")

    # Initialize State Machine
    state_machine = StateMachine()
    print(f"Initial State: {await state_machine.get_current_state()}")

    await state_machine.transition_to("PLANNING")
    print(f"Current State: {await state_machine.get_current_state()}")

    # Initialize Task Queue Engine
    # Ensure the state directory exists for persistence
    os.makedirs("state", exist_ok=True)
    task_queue_engine = TaskQueueEngine("state/task_queue.json")
    await task_queue_engine.load_state() # Load any previous state

    # Create some tasks
    task1 = Task(task_id=TaskID("task_001"), goal="Analyze sales data", created_at=time.time())
    task2 = Task(task_id=TaskID("task_002"), goal="Generate report", dependencies=[TaskID("task_001")], created_at=time.time())
    task3 = Task(task_id=TaskID("task_003"), goal="Deploy model", created_at=time.time())

    await task_queue_engine.add_task(task1)
    await task_queue_engine.add_task(task2)
    await task_queue_engine.add_task(task3)

    print("\n--- Tasks in Queue ---")
    tasks = await task_queue_engine.get_all_tasks()
    for task in tasks:
        print(f"Task ID: {task.task_id}, Goal: {task.goal}, Status: {task.status}, Dependencies: {task.dependencies}")

    # Get next task (should be task1 as it has no dependencies)
    next_task = await task_queue_engine.get_next_task()
    if next_task:
        print(f"\nNext task to execute: {next_task.task_id} - {next_task.goal}")
        await task_queue_engine.update_task_status(next_task.task_id, TaskStatus("EXECUTING"))
        print(f"Updated status of {next_task.task_id} to {TaskStatus('EXECUTING')}")

    # Try to get next task again (should be task3 as task2 depends on task1)
    next_task = await task_queue_engine.get_next_task()
    if next_task:
        print(f"Next task to execute: {next_task.task_id} - {next_task.goal}")
        await task_queue_engine.update_task_status(next_task.task_id, TaskStatus("EXECUTING"))
        print(f"Updated status of {next_task.task_id} to {TaskStatus('EXECUTING')}")

    # Simulate task1 completion
    if next_task and next_task.task_id == TaskID("task_003"):
        await task_queue_engine.update_task_status(TaskID("task_001"), TaskStatus("COMPLETED"))
        print(f"Simulated completion of {TaskID('task_001')}")

    # Now task2 should be available
    next_task = await task_queue_engine.get_next_task()
    if next_task:
        print(f"Next task to execute: {next_task.task_id} - {next_task.goal}")
        await task_queue_engine.update_task_status(next_task.task_id, TaskStatus("EXECUTING"))
        print(f"Updated status of {next_task.task_id} to {TaskStatus('EXECUTING')}")

    await task_queue_engine.persist_state()
    print("Task queue state persisted.")

    print("\n--- Final State of Tasks in Queue ---")
    tasks = await task_queue_engine.get_all_tasks()
    for task in tasks:
        print(f"Task ID: {task.task_id}, Goal: {task.goal}, Status: {task.status}, Dependencies: {task.dependencies}")

    print("--- State Machine & Task Queue Demo End ---")

if __name__ == "__main__":
    # This will fail until StateMachine and TaskQueueEngine are implemented
    try:
        asyncio.run(main())
    except NotImplementedError as e:
        print(f"\nERROR: {e}. Please implement StateMachine and TaskQueueEngine methods first.")

