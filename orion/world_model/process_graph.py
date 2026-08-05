"""
ORION Process Graph
===================

Maps running processes, their relationships, and resource usage.
Uses psutil for cross-platform process monitoring.

Usage:
    graph = ProcessGraph(event_bus)
    await graph.update()
    procs = graph.get_top_cpu(limit=5)
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import psutil

from orion.contracts.agent_contracts import Event
from orion.contracts.world_model_contracts import ProcessNode, WorldModelGraph
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class ProcessGraph:
    """
    Process graph - tracks running processes and their relationships.
    """
    
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._nodes: Dict[int, ProcessNode] = {}
        self._last_update: float = 0
        
        logger.info("ProcessGraph created")
    
    @property
    def process_count(self) -> int:
        return len(self._nodes)
    
    async def update(self) -> int:
        """Scan all running processes and update the graph."""
        self._nodes.clear()
        
        for proc in psutil.process_iter(["pid", "name", "cmdline", "status", "cpu_percent", "memory_percent", "ppid"]):
            try:
                info = proc.info
                node = ProcessNode(
                    pid=info["pid"],
                    name=info["name"] or "unknown",
                    cmdline=info["cmdline"] or [],
                    status=info["status"] or "unknown",
                    cpu_percent=info["cpu_percent"] or 0.0,
                    memory_percent=info["memory_percent"] or 0.0,
                    parent_pid=info["ppid"],
                )
                self._nodes[node.pid] = node
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        self._last_update = time.time()
        
        await self._event_bus.publish(Event(
            event_type="world_model.process.updated",
            payload={"process_count": len(self._nodes), "timestamp": self._last_update},
            timestamp=self._last_update,
            source="process_graph",
        ))
        
        logger.info("Process graph updated: %d processes", len(self._nodes))
        return len(self._nodes)
    
    def get_process(self, pid: int) -> Optional[ProcessNode]:
        """Get a process by PID."""
        return self._nodes.get(pid)
    
    def get_by_name(self, name: str) -> List[ProcessNode]:
        """Find processes by name."""
        return [p for p in self._nodes.values() if name.lower() in p.name.lower()]
    
    def get_children(self, ppid: int) -> List[ProcessNode]:
        """Get child processes of a given PID."""
        return [p for p in self._nodes.values() if p.parent_pid == ppid]
    
    def get_top_cpu(self, limit: int = 10) -> List[ProcessNode]:
        """Get top processes by CPU usage."""
        return sorted(self._nodes.values(), key=lambda p: p.cpu_percent, reverse=True)[:limit]
    
    def get_top_memory(self, limit: int = 10) -> List[ProcessNode]:
        """Get top processes by memory usage."""
        return sorted(self._nodes.values(), key=lambda p: p.memory_percent, reverse=True)[:limit]
    
    def get_running(self) -> List[ProcessNode]:
        """Get all running processes."""
        return [p for p in self._nodes.values() if p.status == "running"]
    
    def get_total_cpu(self) -> float:
        """Get total CPU usage across all processes."""
        return sum(p.cpu_percent for p in self._nodes.values())
    
    def get_total_memory(self) -> float:
        """Get total memory usage across all processes."""
        return sum(p.memory_percent for p in self._nodes.values())
    
    def to_graph(self) -> WorldModelGraph:
        """Export as WorldModelGraph."""
        nodes = [n.model_dump() for n in self._nodes.values()]
        edges = []
        for p in self._nodes.values():
            if p.parent_pid and p.parent_pid in self._nodes:
                edges.append({"from": p.parent_pid, "to": p.pid, "type": "parent_of"})
        
        return WorldModelGraph(
            graph_type="process",
            nodes=nodes,
            edges=edges,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_processes": len(self._nodes),
            "running": len(self.get_running()),
            "total_cpu_percent": round(self.get_total_cpu(), 1),
            "total_memory_percent": round(self.get_total_memory(), 1),
            "last_update": self._last_update,
        }
