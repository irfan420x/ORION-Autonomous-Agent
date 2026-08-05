"""
Tests for ORION World Model Graphs
===================================
"""

import asyncio
import os
import pytest
import time

from orion.core.communication.event_bus import EventBus
from orion.contracts.world_model_contracts import FileNode, ProcessNode, NetworkConnection, WorldModelGraph
from orion.world_model.workspace_graph import WorkspaceGraph
from orion.world_model.process_graph import ProcessGraph
from orion.world_model.network_graph import NetworkGraph


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def workspace(event_bus):
    return WorkspaceGraph(event_bus, max_depth=2, max_nodes=100)


@pytest.fixture
def process_graph(event_bus):
    return ProcessGraph(event_bus)


@pytest.fixture
def network_graph(event_bus):
    return NetworkGraph(event_bus)


# ── Workspace Graph Tests ────────────────────────────────────

class TestWorkspaceGraph:
    @pytest.mark.asyncio
    async def test_scan_directory(self, workspace, tmp_path):
        """Can scan a directory."""
        # Create test files
        (tmp_path / "file1.txt").write_text("hello")
        (tmp_path / "file2.py").write_text("print('hi')")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("world")
        
        count = await workspace.scan(str(tmp_path))
        
        assert count >= 3
        assert workspace.node_count >= 3

    @pytest.mark.asyncio
    async def test_scan_nonexistent(self, workspace):
        """Scan nonexistent path returns 0."""
        count = await workspace.scan("/nonexistent/path")
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_files(self, workspace, tmp_path):
        """get_files returns only files."""
        (tmp_path / "file.txt").write_text("data")
        (tmp_path / "dir").mkdir()
        
        await workspace.scan(str(tmp_path))
        
        files = workspace.get_files()
        assert all(not f.is_dir for f in files)

    @pytest.mark.asyncio
    async def test_get_directories(self, workspace, tmp_path):
        """get_directories returns only directories."""
        (tmp_path / "file.txt").write_text("data")
        (tmp_path / "dir").mkdir()
        
        await workspace.scan(str(tmp_path))
        
        dirs = workspace.get_directories()
        assert all(d.is_dir for d in dirs)

    @pytest.mark.asyncio
    async def test_get_node(self, workspace, tmp_path):
        """Can get a node by path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("data")
        
        await workspace.scan(str(tmp_path))
        
        node = workspace.get_node(str(test_file))
        assert node is not None
        assert node.name == "test.txt"

    @pytest.mark.asyncio
    async def test_find_by_extension(self, workspace, tmp_path):
        """Can find files by extension."""
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "b.py").write_text("y")
        (tmp_path / "c.txt").write_text("z")
        
        await workspace.scan(str(tmp_path))
        
        py_files = workspace.find_by_extension(".py")
        assert len(py_files) == 2

    @pytest.mark.asyncio
    async def test_find_by_name(self, workspace, tmp_path):
        """Can find nodes by name."""
        (tmp_path / "test_file.txt").write_text("data")
        (tmp_path / "other.txt").write_text("data")
        
        await workspace.scan(str(tmp_path))
        
        found = workspace.find_by_name("test")
        assert len(found) >= 1

    @pytest.mark.asyncio
    async def test_total_size(self, workspace, tmp_path):
        """Total size is calculated."""
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")
        
        await workspace.scan(str(tmp_path))
        
        assert workspace.get_total_size() == 10  # 5 + 5

    @pytest.mark.asyncio
    async def test_to_graph(self, workspace, tmp_path):
        """Can export as WorldModelGraph."""
        (tmp_path / "file.txt").write_text("data")
        
        await workspace.scan(str(tmp_path))
        graph = workspace.to_graph()
        
        assert isinstance(graph, WorldModelGraph)
        assert graph.graph_type == "filesystem"
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_stats(self, workspace, tmp_path):
        """Stats are correct."""
        (tmp_path / "file.txt").write_text("data")
        
        await workspace.scan(str(tmp_path))
        stats = workspace.get_stats()
        
        assert "total_nodes" in stats
        assert "files" in stats
        assert "directories" in stats
        assert stats["root"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_max_depth(self, event_bus, tmp_path):
        """Respects max_depth limit."""
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "deep.txt").write_text("deep")
        
        ws = WorkspaceGraph(event_bus, max_depth=2)
        await ws.scan(str(tmp_path))
        
        # Should not reach depth 4
        assert ws.get_node(str(deep / "deep.txt")) is None

    @pytest.mark.asyncio
    async def test_publishes_event(self, event_bus, workspace, tmp_path):
        """Scan publishes event."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("world_model.workspace.scanned", handler)
        (tmp_path / "f.txt").write_text("x")
        await workspace.scan(str(tmp_path))
        
        assert len(events) == 1


# ── Process Graph Tests ──────────────────────────────────────

class TestProcessGraph:
    @pytest.mark.asyncio
    async def test_update(self, process_graph):
        """Can scan running processes."""
        count = await process_graph.update()
        assert count > 0

    @pytest.mark.asyncio
    async def test_get_process(self, process_graph):
        """Can get current process."""
        await process_graph.update()
        
        # Our own process should be there
        pid = os.getpid()
        proc = process_graph.get_process(pid)
        assert proc is not None

    @pytest.mark.asyncio
    async def test_get_by_name(self, process_graph):
        """Can find processes by name."""
        await process_graph.update()
        
        # python3 should be running
        procs = process_graph.get_by_name("python")
        assert len(procs) >= 1

    @pytest.mark.asyncio
    async def test_get_top_cpu(self, process_graph):
        """Can get top CPU processes."""
        await process_graph.update()
        
        top = process_graph.get_top_cpu(5)
        assert len(top) <= 5

    @pytest.mark.asyncio
    async def test_get_top_memory(self, process_graph):
        """Can get top memory processes."""
        await process_graph.update()
        
        top = process_graph.get_top_memory(5)
        assert len(top) <= 5

    @pytest.mark.asyncio
    async def test_get_running(self, process_graph):
        """Can get running processes."""
        await process_graph.update()
        
        running = process_graph.get_running()
        assert len(running) >= 1

    @pytest.mark.asyncio
    async def test_to_graph(self, process_graph):
        """Can export as WorldModelGraph."""
        await process_graph.update()
        graph = process_graph.to_graph()
        
        assert graph.graph_type == "process"
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_stats(self, process_graph):
        """Stats are correct."""
        await process_graph.update()
        stats = process_graph.get_stats()
        
        assert stats["total_processes"] > 0
        assert "total_cpu_percent" in stats

    @pytest.mark.asyncio
    async def test_publishes_event(self, event_bus):
        """Update publishes event."""
        events = []
        async def handler(event):
            events.append(event)
        
        pg = ProcessGraph(event_bus)
        await event_bus.subscribe("world_model.process.updated", handler)
        await pg.update()
        
        assert len(events) == 1


# ── Network Graph Tests ─────────────────────────────────────

class TestNetworkGraph:
    @pytest.mark.asyncio
    async def test_update(self, network_graph):
        """Can scan network connections."""
        count = await network_graph.update()
        assert count >= 0  # May be 0 in some environments

    @pytest.mark.asyncio
    async def test_get_interfaces(self, network_graph):
        """Can get network interfaces."""
        await network_graph.update()
        
        interfaces = network_graph.get_interfaces()
        assert len(interfaces) > 0

    @pytest.mark.asyncio
    async def test_get_active_interfaces(self, network_graph):
        """Can get active interfaces."""
        await network_graph.update()
        
        active = network_graph.get_active_interfaces()
        assert len(active) >= 0

    @pytest.mark.asyncio
    async def test_get_listening(self, network_graph):
        """Can get listening connections."""
        await network_graph.update()
        
        listening = network_graph.get_listening()
        # May be empty in some environments
        assert isinstance(listening, list)

    @pytest.mark.asyncio
    async def test_get_established(self, network_graph):
        """Can get established connections."""
        await network_graph.update()
        
        established = network_graph.get_established()
        assert isinstance(established, list)

    @pytest.mark.asyncio
    async def test_get_open_ports(self, network_graph):
        """Can get open ports."""
        await network_graph.update()
        
        ports = network_graph.get_open_ports()
        assert isinstance(ports, list)

    @pytest.mark.asyncio
    async def test_to_graph(self, network_graph):
        """Can export as WorldModelGraph."""
        await network_graph.update()
        graph = network_graph.to_graph()
        
        assert graph.graph_type == "network"

    @pytest.mark.asyncio
    async def test_stats(self, network_graph):
        """Stats are correct."""
        await network_graph.update()
        stats = network_graph.get_stats()
        
        assert "total_connections" in stats
        assert "interfaces" in stats

    @pytest.mark.asyncio
    async def test_publishes_event(self, event_bus):
        """Update publishes event."""
        events = []
        async def handler(event):
            events.append(event)
        
        ng = NetworkGraph(event_bus)
        await event_bus.subscribe("world_model.network.updated", handler)
        await ng.update()
        
        assert len(events) == 1


# ── Contracts Tests ──────────────────────────────────────────

class TestContracts:
    def test_file_node(self):
        node = FileNode(
            path="/test/file.txt",
            name="file.txt",
            is_dir=False,
            size=100,
        )
        assert node.path == "/test/file.txt"

    def test_process_node(self):
        node = ProcessNode(
            pid=1234,
            name="python3",
            cmdline=["python3", "test.py"],
            status="running",
            cpu_percent=5.0,
            memory_percent=2.0,
        )
        assert node.pid == 1234

    def test_network_connection(self):
        conn = NetworkConnection(
            local_address="0.0.0.0:8080",
            status="LISTEN",
        )
        assert conn.status == "LISTEN"

    def test_world_model_graph(self):
        graph = WorldModelGraph(
            graph_type="test",
            nodes=[{"key": "value"}],
        )
        assert graph.graph_type == "test"
