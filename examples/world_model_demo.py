import asyncio
import os
import time
from orion.world_model.workspace_graph import WorkspaceGraph
from orion.world_model.process_graph import ProcessGraph
from orion.world_model.network_graph import NetworkGraph
from orion.world_model.file_graph import FileGraph
from orion.world_model.git_graph import GitGraph
from orion.world_model.window_graph import WindowGraph
from orion.contracts.world_model_contracts import FileNode, ProcessNode, NetworkConnection, GitStatus, WindowInfo, WorldModelGraph

async def main():
    print("--- World Model Subsystem Demo Start ---")

    # Mock EventBus for graphs to publish updates
    class MockEventBus:
        async def publish(self, event):
            print(f"[MockEventBus] Published: {event.event_type}")

    mock_event_bus = MockEventBus()

    # 1. Workspace Graph
    print("\n--- Workspace Graph ---")
    workspace_graph = WorkspaceGraph(mock_event_bus)
    await workspace_graph.update_graph(path="/home/ubuntu/project/ORION-master")
    workspace_data = await workspace_graph.query_graph("root")
    print(f"Workspace Graph Root: {workspace_data.name}, Children: {[c.name for c in workspace_data.children[:3]]}...")

    # 2. Process Graph
    print("\n--- Process Graph ---")
    process_graph = ProcessGraph(mock_event_bus)
    await process_graph.update_graph()
    process_data = await process_graph.query_graph("top_5_cpu")
    print("Top 5 CPU Processes:")
    for p in process_data:
        print(f"  PID: {p.pid}, Name: {p.name}, CPU: {p.cpu_percent:.2f}%")

    # 3. Network Graph
    print("\n--- Network Graph ---")
    network_graph = NetworkGraph(mock_event_bus)
    await network_graph.update_graph()
    network_data = await network_graph.query_graph("listen_ports")
    print("Listening Ports:")
    for conn in network_data:
        print(f"  {conn.local_address} (PID: {conn.pid})")

    # 4. File Graph (example for a single file)
    print("\n--- File Graph ---")
    file_graph = FileGraph(mock_event_bus)
    await file_graph.update_graph(path="/home/ubuntu/project/ORION-master/BUILD_GUIDE.md")
    file_data = await file_graph.query_graph("metadata")
    print(f"File: {file_data.name}, Size: {file_data.size} bytes, Modified: {time.ctime(file_data.last_modified)}")

    # 5. Git Graph
    print("\n--- Git Graph ---")
    git_graph = GitGraph(mock_event_bus)
    # Assuming the current directory is a git repo
    await git_graph.update_graph(repo_path="/home/ubuntu/project/ORION-master")
    git_data = await git_graph.query_graph("status")
    print(f"Git Repo Status: Dirty: {git_data.is_dirty}, Branch: {git_data.current_branch}, Last Commit: {git_data.last_commit_msg[:50]}...")

    # 6. Window Graph (mocked for sandbox environment)
    print("\n--- Window Graph (Mocked) ---")
    window_graph = WindowGraph(mock_event_bus)
    await window_graph.update_graph()
    window_data = await window_graph.query_graph("active_windows")
    if window_data:
        print("Active Windows:")
        for win in window_data:
            print(f"  Title: {win.title}, Process: {win.process_name}")
    else:
        print("No active windows detected (or mocked data). ")

    print("--- World Model Subsystem Demo End ---")

if __name__ == "__main__":
    # This will fail until World Model modules are implemented
    try:
        asyncio.run(main())
    except NotImplementedError as e:
        print(f"\nERROR: {e}. Please implement World Model module methods first.")
