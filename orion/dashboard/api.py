"""
ORION Dashboard Server
======================

Web-based dashboard for ORION Autonomous Agent.
Provides real-time system monitoring, task management,
memory visualization, and control panel.

Usage:
    python -m orion.dashboard.server
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import psutil

logger = logging.getLogger(__name__)


class DashboardAPI:
    """API endpoints for the dashboard."""
    
    def __init__(self, event_bus=None, memory_manager=None, task_queue=None, runtime=None):
        self._event_bus = event_bus
        self._memory = memory_manager
        self._task_queue = task_queue
        self._runtime = runtime
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview data."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network
        net = psutil.net_io_counters()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(),
                "freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            },
            "memory": {
                "percent": memory.percent,
                "used_gb": round(memory.used / (1024**3), 1),
                "total_gb": round(memory.total / (1024**3), 1),
            },
            "disk": {
                "percent": disk.percent,
                "used_gb": round(disk.used / (1024**3), 1),
                "total_gb": round(disk.total / (1024**3), 1),
            },
            "network": {
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
            },
            "uptime": time.time() - psutil.boot_time(),
            "status": "OPTIMAL" if cpu_percent < 80 and memory.percent < 80 else "WARNING",
        }
    
    def get_processes(self, limit: int = 20) -> list:
        """Get top processes by CPU usage."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] and pinfo['cpu_percent'] > 0:
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu": round(pinfo['cpu_percent'], 1),
                        "memory": round(pinfo['memory_percent'] or 0, 1),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:limit]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        if self._memory:
            return self._memory.get_stats()
        return {
            "session_count": 0,
            "working_count": 0,
            "long_term_count": 0,
            "total_stores": 0,
        }
    
    def get_tasks(self) -> list:
        """Get current tasks."""
        if self._task_queue:
            tasks = self._task_queue.list_tasks()
            return [
                {
                    "id": t.task_id,
                    "goal": t.goal,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "progress": getattr(t, 'progress', 0),
                }
                for t in tasks[:10]
            ]
        return []
    
    def get_runtime_status(self) -> Dict[str, Any]:
        """Get runtime status."""
        if self._runtime:
            return self._runtime.get_status()
        return {
            "mode": "unknown",
            "modules_loaded": 0,
            "modules_total": 0,
        }
    
    def get_navigation_items(self) -> list:
        """Get sidebar navigation items."""
        return [
            {"id": "dashboard", "label": "DASHBOARD", "icon": "📊", "active": True},
            {"id": "agent", "label": "AGENT", "icon": "🤖"},
            {"id": "tasks", "label": "TASKS", "icon": "📋"},
            {"id": "memory", "label": "MEMORY", "icon": "🧠"},
            {"id": "world", "label": "WORLD MODEL", "icon": "🌐"},
            {"id": "tools", "label": "TOOLS", "icon": "🔧"},
            {"id": "terminal", "label": "TERMINAL", "icon": "💻"},
            {"id": "settings", "label": "SETTINGS", "icon": "⚙️"},
        ]
    
    def get_quick_actions(self) -> list:
        """Get quick action buttons."""
        return [
            {"id": "launch_app", "label": "Launch App", "icon": "🚀"},
            {"id": "search_web", "label": "Search Web", "icon": "🔍"},
            {"id": "open_terminal", "label": "Open Terminal", "icon": "💻"},
            {"id": "open_notes", "label": "Open Notes", "icon": "📝"},
            {"id": "voice_cmd", "label": "Voice Command", "icon": "🎙️"},
            {"id": "screenshot", "label": "Screenshot", "icon": "📸"},
            {"id": "file_manager", "label": "File Manager", "icon": "📁"},
            {"id": "sys_monitor", "label": "System Monitor", "icon": "📈"},
        ]
    
    def get_schedule(self) -> list:
        """Get today's schedule (placeholder)."""
        return [
            {"time": "09:00", "title": "Project Meeting", "type": "meeting"},
            {"time": "11:30", "title": "Code Review", "type": "work"},
            {"time": "14:00", "title": "Research Session", "type": "research"},
            {"time": "16:00", "title": "Client Call", "type": "meeting"},
            {"time": "18:30", "title": "Gym Time", "type": "personal"},
        ]
    
    def get_dock_apps(self) -> list:
        """Get dock application shortcuts."""
        return [
            {"id": "terminal", "label": "Terminal", "icon": "💻"},
            {"id": "browser", "label": "Browser", "icon": "🌐"},
            {"id": "vscode", "label": "VS Code", "icon": "📝"},
            {"id": "files", "label": "Files", "icon": "📁"},
            {"id": "orion", "label": "ORION", "icon": "⚡"},
            {"id": "notes", "label": "Notes", "icon": "📋"},
            {"id": "calendar", "label": "Calendar", "icon": "📅"},
            {"id": "music", "label": "Music", "icon": "🎵"},
            {"id": "chat", "label": "AI Chat", "icon": "💬"},
        ]
    
    def execute_action(self, action_id: str, params: Dict = None) -> Dict[str, Any]:
        """Execute a quick action."""
        import subprocess
        
        actions = {
            "open_terminal": lambda: subprocess.Popen(["x-terminal-emulator"]),
            "open_notes": lambda: subprocess.Popen(["xdg-open", "https://notion.so"]),
            "file_manager": lambda: subprocess.Popen(["xdg-open", os.path.expanduser("~")]),
            "screenshot": lambda: subprocess.Popen(["gnome-screenshot"]),
        }
        
        if action_id in actions:
            try:
                actions[action_id]()
                return {"success": True, "message": f"Executed: {action_id}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": f"Unknown action: {action_id}"}
