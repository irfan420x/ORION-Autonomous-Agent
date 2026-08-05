"""
ORION Workspace Graph
=====================

Represents the filesystem structure as a graph.
Scans directories and tracks files, sizes, and relationships.

Usage:
    graph = WorkspaceGraph(event_bus)
    await graph.scan("/home/user/project")
    files = graph.get_files()
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from orion.contracts.agent_contracts import Event
from orion.contracts.world_model_contracts import FileNode, WorldModelGraph
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class WorkspaceGraph:
    """
    Filesystem graph - tracks files, directories, and their relationships.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        max_depth: int = 5,
        max_nodes: int = 5000,
        ignore_patterns: Optional[Set[str]] = None,
    ):
        self._event_bus = event_bus
        self._max_depth = max_depth
        self._max_nodes = max_nodes
        self._ignore = ignore_patterns or {
            "__pycache__", ".git", "node_modules", ".venv", "venv",
            ".pytest_cache", ".mypy_cache", "dist", "build",
        }
        
        self._nodes: Dict[str, FileNode] = {}
        self._root: Optional[str] = None
        self._last_scan: float = 0
        
        logger.info("WorkspaceGraph created")
    
    @property
    def root(self) -> Optional[str]:
        return self._root
    
    @property
    def node_count(self) -> int:
        return len(self._nodes)
    
    async def scan(self, path: str) -> int:
        """
        Scan a directory and build the graph.
        Returns the number of nodes added.
        """
        path = os.path.abspath(path)
        if not os.path.exists(path):
            logger.warning("Path does not exist: %s", path)
            return 0
        
        self._root = path
        self._nodes.clear()
        
        count = await self._scan_directory(path, depth=0)
        self._last_scan = time.time()
        
        # Publish event
        await self._event_bus.publish(Event(
            event_type="world_model.workspace.scanned",
            payload={
                "root": path,
                "node_count": count,
                "timestamp": self._last_scan,
            },
            timestamp=self._last_scan,
            source="workspace_graph",
        ))
        
        logger.info("Workspace scanned: %s (%d nodes)", path, count)
        return count
    
    async def _scan_directory(self, path: str, depth: int) -> int:
        """Recursively scan a directory."""
        if depth > self._max_depth:
            return 0
        if len(self._nodes) >= self._max_nodes:
            return 0
        
        count = 0
        
        try:
            entries = list(os.scandir(path))
        except PermissionError:
            return 0
        
        children = []
        
        for entry in entries:
            if entry.name.startswith(".") and entry.name in self._ignore:
                continue
            if entry.name in self._ignore:
                continue
            if len(self._nodes) >= self._max_nodes:
                break
            
            try:
                stat = entry.stat()
                is_dir = entry.is_dir(follow_symlinks=False)
                
                node = FileNode(
                    path=entry.path,
                    name=entry.name,
                    is_dir=is_dir,
                    size=stat.st_size if not is_dir else None,
                    last_modified=stat.st_mtime,
                    children=None,
                )
                
                self._nodes[entry.path] = node
                children.append(entry.path)
                count += 1
                
                if is_dir:
                    sub_count = await self._scan_directory(entry.path, depth + 1)
                    count += sub_count
                    
                    # Update children list
                    if entry.path in self._nodes:
                        sub_children = [
                            p for p in self._nodes
                            if os.path.dirname(p) == entry.path
                        ]
                        self._nodes[entry.path] = FileNode(
                            path=entry.path,
                            name=entry.name,
                            is_dir=True,
                            size=None,
                            last_modified=stat.st_mtime,
                            children=sub_children,
                        )
            
            except (PermissionError, OSError):
                continue
        
        return count
    
    def get_node(self, path: str) -> Optional[FileNode]:
        """Get a node by path."""
        return self._nodes.get(path)
    
    def get_files(self) -> List[FileNode]:
        """Get all file nodes (not directories)."""
        return [n for n in self._nodes.values() if not n.is_dir]
    
    def get_directories(self) -> List[FileNode]:
        """Get all directory nodes."""
        return [n for n in self._nodes.values() if n.is_dir]
    
    def get_children(self, path: str) -> List[FileNode]:
        """Get direct children of a directory."""
        node = self._nodes.get(path)
        if not node or not node.is_dir or not node.children:
            return []
        return [self._nodes[c] for c in node.children if c in self._nodes]
    
    def get_total_size(self) -> int:
        """Get total size of all files."""
        return sum(n.size or 0 for n in self._nodes.values() if not n.is_dir)
    
    def find_by_extension(self, ext: str) -> List[FileNode]:
        """Find files by extension."""
        return [n for n in self.get_files() if n.name.endswith(ext)]
    
    def find_by_name(self, name: str) -> List[FileNode]:
        """Find nodes by name (partial match)."""
        return [n for n in self._nodes.values() if name.lower() in n.name.lower()]
    
    def to_graph(self) -> WorldModelGraph:
        """Export as WorldModelGraph."""
        nodes = [n.model_dump() for n in self._nodes.values()]
        edges = []
        for node in self._nodes.values():
            if node.children:
                for child in node.children:
                    edges.append({"from": node.path, "to": child, "type": "contains"})
        
        return WorldModelGraph(
            graph_type="filesystem",
            nodes=nodes,
            edges=edges,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        files = self.get_files()
        dirs = self.get_directories()
        return {
            "root": self._root,
            "total_nodes": len(self._nodes),
            "files": len(files),
            "directories": len(dirs),
            "total_size_bytes": self.get_total_size(),
            "total_size_mb": round(self.get_total_size() / (1024 * 1024), 2),
            "last_scan": self._last_scan,
            "max_depth": self._max_depth,
        }
