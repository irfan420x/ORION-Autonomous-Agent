"""
ORION Executor Agent
====================

Executes individual tasks. Can run shell commands,
interact with tools, and report results.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from orion.contracts.agent_contracts import Event, Task, TaskStatus
from orion.core.communication.event_bus import EventBus
from orion.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ExecutorAgent(BaseAgent):
    """
    Task execution agent.
    
    Responsibilities:
    - Execute assigned tasks
    - Run shell commands safely
    - Report results back to Orchestrator
    """
    
    # Safe commands that can be executed
    SAFE_COMMANDS = [
        "ls", "cat", "head", "tail", "grep", "find", "wc",
        "echo", "date", "whoami", "pwd", "df", "du", "free",
        "uname", "hostname", "uptime", "ps", "top",
    ]
    
    def __init__(self, event_bus: EventBus):
        super().__init__(
            agent_id="executor",
            event_bus=event_bus,
            capabilities=["execute", "shell", "file_ops"],
        )
    
    async def execute_task(self, task: Task) -> Any:
        """
        Execute a task based on its goal.
        """
        goal = task.goal.lower()
        
        logger.info("Executor executing: %s", task.goal)
        
        # Simple task routing based on keywords
        if any(cmd in goal for cmd in ["list", "show", "ls", "dir"]):
            return await self._run_command("ls -la")
        
        elif any(cmd in goal for cmd in ["disk", "space", "storage"]):
            return await self._run_command("df -h")
        
        elif any(cmd in goal for cmd in ["memory", "ram"]):
            return await self._run_command("free -h")
        
        elif any(cmd in goal for cmd in ["process", "running"]):
            return await self._run_command("ps aux | head -20")
        
        elif any(cmd in goal for cmd in ["time", "date"]):
            return await self._run_command("date")
        
        elif any(cmd in goal for cmd in ["hostname", "machine"]):
            return await self._run_command("hostname")
        
        else:
            # Default: acknowledge the task
            return f"Task acknowledged: {task.goal}"
    
    async def _run_command(self, command: str) -> str:
        """Run a safe shell command."""
        # Verify command is safe
        cmd_base = command.split()[0] if command else ""
        if cmd_base not in self.SAFE_COMMANDS:
            return f"⛔ Command not allowed: {cmd_base}"
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            
            output = stdout.decode().strip()
            if not output and stderr:
                output = stderr.decode().strip()
            
            return output or "(no output)"
        
        except asyncio.TimeoutError:
            return f"⏱️ Command timed out: {command}"
        except Exception as e:
            return f"❌ Error: {e}"
