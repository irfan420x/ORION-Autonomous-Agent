"""
ORION Network Graph
===================

Maps network connections, open ports, and active interfaces.
Uses psutil for cross-platform network monitoring.

Usage:
    graph = NetworkGraph(event_bus)
    await graph.update()
    conns = graph.get_listening()
"""

import asyncio
import logging
import socket
import time
from typing import Any, Dict, List, Optional

import psutil

from orion.contracts.agent_contracts import Event
from orion.contracts.world_model_contracts import NetworkConnection, WorldModelGraph
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class NetworkGraph:
    """
    Network graph - tracks connections, ports, and interfaces.
    """
    
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._connections: List[NetworkConnection] = []
        self._interfaces: Dict[str, Dict[str, Any]] = {}
        self._last_update: float = 0
        
        logger.info("NetworkGraph created")
    
    @property
    def connection_count(self) -> int:
        return len(self._connections)
    
    async def update(self) -> int:
        """Scan network connections and interfaces."""
        self._connections.clear()
        
        # Get connections
        for conn in psutil.net_connections(kind="inet"):
            try:
                local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown"
                remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
                
                nc = NetworkConnection(
                    local_address=local,
                    remote_address=remote,
                    status=conn.status or "UNKNOWN",
                    pid=conn.pid,
                )
                self._connections.append(nc)
            except (AttributeError, ValueError):
                continue
        
        # Get interfaces
        self._interfaces.clear()
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for name, addr_list in addrs.items():
            self._interfaces[name] = {
                "addresses": [str(a.address) for a in addr_list],
                "is_up": stats.get(name, None) and stats[name].isup,
                "speed_mbps": stats.get(name, None) and stats[name].speed,
            }
        
        self._last_update = time.time()
        
        await self._event_bus.publish(Event(
            event_type="world_model.network.updated",
            payload={
                "connections": len(self._connections),
                "interfaces": len(self._interfaces),
                "timestamp": self._last_update,
            },
            timestamp=self._last_update,
            source="network_graph",
        ))
        
        logger.info("Network graph updated: %d connections, %d interfaces",
                    len(self._connections), len(self._interfaces))
        return len(self._connections)
    
    def get_listening(self) -> List[NetworkConnection]:
        """Get all listening connections."""
        return [c for c in self._connections if c.status == "LISTEN"]
    
    def get_established(self) -> List[NetworkConnection]:
        """Get all established connections."""
        return [c for c in self._connections if c.status == "ESTABLISHED"]
    
    def get_by_pid(self, pid: int) -> List[NetworkConnection]:
        """Get connections for a specific PID."""
        return [c for c in self._connections if c.pid == pid]
    
    def get_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """Get network interfaces."""
        return self._interfaces
    
    def get_active_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """Get only active (up) interfaces."""
        return {k: v for k, v in self._interfaces.items() if v.get("is_up")}
    
    def get_open_ports(self) -> List[int]:
        """Get all open (listening) ports."""
        ports = []
        for c in self._connections:
            if c.status == "LISTEN":
                try:
                    port = int(c.local_address.split(":")[-1])
                    if port not in ports:
                        ports.append(port)
                except (ValueError, IndexError):
                    pass
        return sorted(ports)
    
    def to_graph(self) -> WorldModelGraph:
        """Export as WorldModelGraph."""
        nodes = [c.model_dump() for c in self._connections]
        return WorldModelGraph(
            graph_type="network",
            nodes=nodes,
            edges=[],
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_connections": len(self._connections),
            "listening": len(self.get_listening()),
            "established": len(self.get_established()),
            "open_ports": self.get_open_ports(),
            "interfaces": len(self._interfaces),
            "active_interfaces": len(self.get_active_interfaces()),
            "last_update": self._last_update,
        }
