"""
ORION Telegram Bot Integration
=============================

Telegram bot that connects to ORION's EventBus, StateMachine, TaskQueue, and MemoryManager.

Usage:
    python -m orion.remote_control.telegram_bot
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from orion.contracts.agent_contracts import Event, Task
from orion.contracts.memory_contracts import MemoryType
from orion.core.communication.event_bus import EventBus, get_event_bus
from orion.core.state.state_machine import StateMachine, State
from orion.core.state.task_queue import TaskQueueEngine
from orion.core.runtime.runtime import AdaptiveRuntime
from orion.memory.memory_manager import MemoryManager
from orion.reliability.health_monitor import HealthMonitor
from orion.reliability.self_healer import SelfHealer
from orion.intelligence.llm_client import LLMClient, LLMMessage

logger = logging.getLogger(__name__)


class OrionTelegramBot:
    """Telegram bot integration for ORION."""
    
    def __init__(
        self,
        token: str,
        allowed_user_id: int,
        event_bus: Optional[EventBus] = None,
        state_machine: Optional[StateMachine] = None,
        task_queue: Optional[TaskQueueEngine] = None,
        memory_manager: Optional[MemoryManager] = None,
        runtime: Optional[AdaptiveRuntime] = None,
        health_monitor: Optional[HealthMonitor] = None,
        self_healer: Optional[SelfHealer] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.token = token
        self.allowed_user_id = allowed_user_id
        self.event_bus = event_bus or get_event_bus()
        self.state_machine = state_machine
        self.task_queue = task_queue
        self.memory_manager = memory_manager
        self.runtime = runtime
        self.health_monitor = health_monitor
        self.self_healer = self_healer
        self.llm_client = llm_client
        self.app: Optional[Application] = None
        
        # Conversation history (per user)
        self._conversation_history: Dict[int, List[Dict[str, str]]] = {}
        self._max_history: int = 20
        
        # ORION system prompt with tool awareness
        self._system_prompt = """You are ORION, an Autonomous Adaptive OS Agent created by IRFAN. You are a powerful AI assistant integrated into a Linux system.

YOUR CAPABILITIES (use these tools when the user asks):
1. **System Info** - Check CPU, RAM, disk, processes, network
2. **Health Check** - Check system health and services
3. **Memory** - Remember and recall information
4. **Tasks** - Add, list, complete tasks
5. **State** - Check and change agent state
6. **Runtime** - Check runtime mode, modules, resources
7. **File Operations** - Read, write, search files
8. **Process Management** - List, kill processes

YOUR PERSONALITY:
- Helpful, friendly, and professional
- Concise but thorough responses
- Use emojis appropriately
- Respond in the same language the user writes in (Bengali/English)
- If you can't do something, say so honestly
- When you use a tool, explain what you did

IMPORTANT RULES:
- ALWAYS use tools when the user asks for system information or actions
- When user asks to CREATE a file, use the create_file tool immediately - do NOT just show code
- When user asks to RUN a command, use run_shell_command tool
- When working with files, always use FULL PATHS (e.g., ~/Desktop/file.py or /home/irfan/Desktop/file.py)
- The home directory is /home/irfan
- Desktop is at ~/Desktop/
- Don't make up information - use tools to get real data
- Be proactive - if a task needs multiple steps, do them all
- Keep responses under 500 words unless asked for more detail
- When you use a tool, briefly explain what you did"""

        # Tool definitions for LLM function calling
        self._tools = [
            {
                "name": "get_system_info",
                "description": "Get system information: CPU, RAM, disk, processes. Use when user asks about system status, resources, or performance.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_health_status",
                "description": "Check system health and service status. Use when user asks about health, services, or system stability.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_runtime_status",
                "description": "Get ORION runtime status: operating mode, loaded modules, resource usage. Use when user asks about ORION status or capabilities.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "remember",
                "description": "Store information in memory for later recall. Use when user says 'remember this' or shares important info.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "What to remember (e.g., 'user_name', 'project_deadline')"},
                        "value": {"type": "string", "description": "The information to store"}
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "recall",
                "description": "Recall stored information from memory. Use when user asks 'what do you remember about X' or 'recall X'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to recall (e.g., 'user_name', 'project info')"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_task",
                "description": "Add a new task to the task queue. Use when user wants to create or schedule a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "Task description/goal"}
                    },
                    "required": ["goal"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List all tasks in the queue. Use when user asks about tasks, todo list, or pending work.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "create_file",
                "description": "Create a file with content. Use when user asks to create, write, or make a file. ALWAYS use this tool when user asks to create a file - do NOT just show code, actually create it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Full file path (e.g., /home/irfan/Desktop/file.py)"},
                        "content": {"type": "string", "description": "File content to write"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "run_shell_command",
                "description": "Execute a shell command on the system. Use when user asks to run a command, check file, or do system operation. ONLY use safe commands.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute (must be safe)"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search through all memory tiers. Use when user asks to find information stored in memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_time_date",
                "description": "Get current time and date. Use when user asks about time, date, or day.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        logger.info("OrionTelegramBot initialized for user %d", allowed_user_id)
    
    # ========================================================================
    # Tool Execution (called by LLM)
    # ========================================================================
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result as string."""
        try:
            if tool_name == "get_system_info":
                return await self._tool_system_info()
            elif tool_name == "get_health_status":
                return await self._tool_health_status()
            elif tool_name == "get_runtime_status":
                return await self._tool_runtime_status()
            elif tool_name == "remember":
                return await self._tool_remember(arguments["key"], arguments["value"])
            elif tool_name == "recall":
                return await self._tool_recall(arguments["query"])
            elif tool_name == "add_task":
                return await self._tool_add_task(arguments["goal"])
            elif tool_name == "list_tasks":
                return await self._tool_list_tasks()
            elif tool_name == "create_file":
                return await self._tool_create_file(arguments["path"], arguments["content"])
            elif tool_name == "run_shell_command":
                return await self._tool_run_command(arguments["command"])
            elif tool_name == "search_memory":
                return await self._tool_search_memory(arguments["query"])
            elif tool_name == "get_time_date":
                import datetime
                now = datetime.datetime.now()
                return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})"
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool error ({tool_name}): {str(e)}"
    
    async def _tool_system_info(self) -> str:
        """Get system information."""
        import psutil
        cpu = psutil.cpu_percent(interval=0)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return (
            f"📊 **System Information:**\n"
            f"• CPU: {cpu}% ({psutil.cpu_count()} cores)\n"
            f"• RAM: {ram.percent}% ({round(ram.used/1024**3, 1)}/{round(ram.total/1024**3, 1)} GB)\n"
            f"• Disk: {disk.percent}% ({round(disk.used/1024**3, 1)}/{round(disk.total/1024**3, 1)} GB)\n"
            f"• Processes: {len(psutil.pids())}\n"
            f"• Uptime: {round(psutil.time.time() - psutil.boot_time())}s"
        )
    
    async def _tool_health_status(self) -> str:
        """Check health status."""
        if self.health_monitor:
            report = await self.health_monitor.check_all()
            lines = [f"🏥 **Health: {report.overall_status.value}**\n"]
            for svc in report.services:
                icon = "🟢" if svc.status.value == "HEALTHY" else "🔴"
                lines.append(f"{icon} {svc.service_name}: {svc.status.value}")
            return "\n".join(lines)
        return "❌ Health monitor not available"
    
    async def _tool_runtime_status(self) -> str:
        """Get runtime status."""
        if self.runtime:
            stats = self.runtime.get_stats()
            return (
                f"⚡ **Runtime Status:**\n"
                f"• Mode: {stats['current_mode']}\n"
                f"• Modules: {stats['loaded_module_count']}/{stats['total_module_count']}\n"
                f"• Uptime: {stats['uptime_seconds']:.0f}s\n"
                f"• Feasible modes: {', '.join(stats['feasible_modes'])}"
            )
        return "❌ Runtime not available"
    
    async def _tool_remember(self, key: str, value: str) -> str:
        """Store in memory."""
        if self.memory_manager:
            await self.memory_manager.remember(key, value, memory_type="long_term")
            return f"✅ Remembered: {key} = {value}"
        return "❌ Memory not available"
    
    async def _tool_recall(self, query: str) -> str:
        """Recall from memory."""
        if self.memory_manager:
            results = await self.memory_manager.recall_all(query)
            if results:
                items = [f"• {r.get('key', '?')}: {r.get('value', '?')}" for r in results[:5]]
                return f"🧠 **Recalled:**\n" + "\n".join(items)
            return f"Nothing found for: {query}"
        return "❌ Memory not available"
    
    async def _tool_add_task(self, goal: str) -> str:
        """Add a task."""
        if self.task_queue:
            import time as t
            from orion.contracts.agent_contracts import Task, TaskID
            task_id = TaskID(f"task_{int(t.time())}")
            task = Task(task_id=task_id, goal=goal, created_at=t.time(), updated_at=t.time())
            await self.task_queue.add_task(task)
            return f"✅ Task added: {goal} (ID: {task_id})"
        return "❌ Task queue not available"
    
    async def _tool_list_tasks(self) -> str:
        """List tasks."""
        if self.task_queue:
            tasks = await self.task_queue.get_all_tasks()
            if not tasks:
                return "📋 No tasks in queue"
            lines = ["📋 **Tasks:**"]
            for t in tasks[:10]:
                lines.append(f"• {t.task_id}: {t.goal} [{t.status}]")
            return "\n".join(lines)
        return "❌ Task queue not available"
    
    async def _tool_run_command(self, command: str) -> str:
        """Run a safe shell command."""
        # Safety: block dangerous commands
        dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/", "chmod 777", "shutdown", "reboot"]
        for d in dangerous:
            if d in command.lower():
                return f"⛔ Blocked dangerous command: {command}"
        
        import asyncio
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.expanduser("~"),  # Run from home directory
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            output = stdout.decode()[:1500] or stderr.decode()[:500] or "(no output)"
            return f"💻 `{command}`\n```\n{output}\n```"
        except asyncio.TimeoutError:
            return f"⏱️ Command timed out: {command}"
        except Exception as e:
            return f"❌ Command error: {e}"
    
    async def _tool_search_memory(self, query: str) -> str:
        """Search memory."""
        if self.memory_manager:
            results = await self.memory_manager.search_all(query)
            if results:
                items = [f"• {r.get('key', '?')}: {str(r.get('value', '?'))[:100]}" for r in results[:5]]
                return f"🔍 **Search results:**\n" + "\n".join(items)
            return f"No results for: {query}"
        return "❌ Memory not available"
    
    async def _tool_create_file(self, path: str, content: str) -> str:
        """Create a file with content."""
        import os
        
        # Expand ~ to home directory
        path = os.path.expanduser(path)
        
        # Create directory if needed
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(path, 'w') as f:
            f.write(content)
        
        # Make executable if it's a script
        if path.endswith('.py') or path.endswith('.sh'):
            os.chmod(path, 0o755)
        
        return f"✅ File created: {path} ({len(content)} bytes)"
    
    # ========================================================================
    # Basic Commands
    # ========================================================================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        await update.message.reply_text(
            "🤖 **ORION Autonomous Agent**\n\n"
            "📋 **Commands:**\n"
            "/help - Show all commands\n"
            "/status - System status\n"
            "/ping - Test connection\n\n"
            "🔄 **State:** /state, /setstate\n"
            "📝 **Tasks:** /tasks, /addtask, /task\n"
            "🧠 **Memory:** /memory, /remember, /recall\n"
            "📡 **Events:** /events, /stats\n"
            "⚡ **Runtime:** /runtime, /resources, /modules, /setmode",
            parse_mode="Markdown"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        await update.message.reply_text(
            "📋 **All Commands:**\n\n"
            "**Basic:** /start, /help, /status, /ping\n\n"
            "**State Machine:**\n"
            "/state - Current state\n"
            "/transitions - Valid transitions\n"
            "/setstate <state> - Change state\n\n"
            "**Task Queue:**\n"
            "/tasks - List tasks\n"
            "/addtask <goal> - Add task\n"
            "/task <id> - Task details\n"
            "/completetask <id> - Mark complete\n"
            "/failedtask <id> - Mark failed\n"
            "/removetask <id> - Remove task\n"
            "/cleartasks - Clear completed\n\n"
            "**Memory:**\n"
            "/memory - Memory stats\n"
            "/remember <key> <value> - Store\n"
            "/recall <key> - Retrieve\n"
            "/forget <key> - Delete\n"
            "/searchmemory <query> - Search\n"
            "/logexperience <action> <outcome> - Log\n"
            "/lessons - Get lessons learned\n\n"
            "**EventBus:**\n"
            "/events - Recent events\n"
            "/stats - System statistics\n\n"
            "**Adaptive Runtime:**\n"
            "/runtime - Runtime status & hardware\n"
            "/resources - CPU, RAM, disk usage\n"
            "/modules - Loaded modules list\n"
            "/setmode <mode> - Switch operating mode",
            parse_mode="Markdown"
        )
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        start_time = time.time()
        msg = await update.message.reply_text("🏓 Pong!")
        elapsed = (time.time() - start_time) * 1000
        await msg.edit_text(f"🏓 Pong! ({elapsed:.0f}ms)")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        lines = ["📊 **ORION System Status**\n"]
        
        if self.state_machine:
            sm_stats = self.state_machine.get_stats()
            lines.append("🔄 **State Machine:**")
            lines.append(f"  • Current: `{sm_stats['current_state']}`")
            lines.append(f"  • Transitions: {sm_stats['total_transitions']}")
            lines.append("")
        
        if self.task_queue:
            tq_stats = self.task_queue.get_stats()
            lines.append("📝 **Task Queue:**")
            lines.append(f"  • Total: {tq_stats['total_tasks']}")
            for status, count in tq_stats.get('status_counts', {}).items():
                lines.append(f"  • {status}: {count}")
            lines.append("")
        
        if self.memory_manager:
            mem_stats = self.memory_manager.get_stats()
            lines.append("🧠 **Memory:**")
            lines.append(f"  • Session: {mem_stats['session']['total_entries']} entries")
            lines.append(f"  • Long-term: {mem_stats['long_term']['total_entries']} entries")
            lines.append(f"  • Episodes: {mem_stats['episodic']['total_episodes']}")
            lines.append(f"  • Semantic: {mem_stats['semantic']['total_documents']} docs")
            lines.append("")
        
        eb_stats = self.event_bus.get_stats()
        lines.append("📡 **EventBus:**")
        lines.append(f"  • Published: {eb_stats['total_published']}")
        lines.append(f"  • Delivered: {eb_stats['total_delivered']}")
        lines.append(f"  • Errors: {eb_stats['total_errors']}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        eb_stats = self.event_bus.get_stats()
        await update.message.reply_text(
            "📈 **EventBus Statistics:**\n\n"
            f"• Published: {eb_stats['total_published']}\n"
            f"• Delivered: {eb_stats['total_delivered']}\n"
            f"• Errors: {eb_stats['total_errors']}\n"
            f"• Subscriptions: {eb_stats['active_subscriptions']}",
            parse_mode="Markdown"
        )
    
    # ========================================================================
    # State Machine Commands
    # ========================================================================
    
    async def state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.state_machine:
            await update.message.reply_text("❌ State Machine not initialized")
            return
        
        stats = self.state_machine.get_stats()
        await update.message.reply_text(
            f"🔄 **Current State:** `{stats['current_state']}`\n\n"
            f"**Valid transitions:** {', '.join(f'`{s}`' for s in stats['valid_transitions']) or 'None'}\n"
            f"**Total transitions:** {stats['total_transitions']}",
            parse_mode="Markdown"
        )
    
    async def transitions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.state_machine:
            await update.message.reply_text("❌ State Machine not initialized")
            return
        
        current = self.state_machine.current_state
        all_transitions = StateMachine.VALID_TRANSITIONS
        
        lines = ["🔄 **State Transitions:**\n"]
        for state, targets in all_transitions.items():
            marker = " ← **current**" if state == current else ""
            targets_str = ", ".join(f"`{t.value}`" for t in targets) or "None"
            lines.append(f"• `{state.value}`{marker} → {targets_str}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def setstate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.state_machine:
            await update.message.reply_text("❌ State Machine not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text(
                "Usage: `/setstate <state>`\nStates: IDLE, PROCESSING, PAUSED, ERROR, SHUTDOWN",
                parse_mode="Markdown"
            )
            return
        
        state_name = args[0].upper()
        reason = " ".join(args[1:]) if len(args) > 1 else "Manual change via Telegram"
        
        try:
            new_state = State(state_name)
        except ValueError:
            await update.message.reply_text(f"❌ Invalid state: `{state_name}`", parse_mode="Markdown")
            return
        
        success = await self.state_machine.transition_to(new_state, reason=reason)
        
        if success:
            await update.message.reply_text(
                f"✅ State changed to `{new_state.value}`\nReason: {reason}",
                parse_mode="Markdown"
            )
        else:
            valid = self.state_machine.get_valid_transitions()
            await update.message.reply_text(
                f"❌ Invalid transition: `{self.state_machine.current_state.value}` → `{new_state.value}`\n"
                f"Valid: {', '.join(f'`{s.value}`' for s in valid)}",
                parse_mode="Markdown"
            )
    
    # ========================================================================
    # Task Queue Commands
    # ========================================================================
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        filter_status = args[0].upper() if args else None
        
        if filter_status:
            tasks = await self.task_queue.get_tasks_by_status(filter_status)
        else:
            tasks = await self.task_queue.get_all_tasks()
        
        if not tasks:
            await update.message.reply_text("📭 No tasks found")
            return
        
        lines = [f"📝 **Tasks ({len(tasks)}):**\n"]
        for task in tasks[:20]:
            status_emoji = {
                "PENDING": "⏳", "IN_PROGRESS": "🔄", "COMPLETED": "✅",
                "FAILED": "❌", "CANCELLED": "🚫",
            }.get(task.status, "❓")
            lines.append(f"{status_emoji} `{task.task_id}` - {task.goal[:50]}")
        
        if len(tasks) > 20:
            lines.append(f"\n... and {len(tasks) - 20} more")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def addtask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/addtask <goal>`", parse_mode="Markdown")
            return
        
        goal = " ".join(args)
        task_id = f"task_{int(time.time())}"
        
        task = Task(
            task_id=task_id, goal=goal, status="PENDING",
            dependencies=[], created_at=time.time(), updated_at=time.time(),
        )
        
        await self.task_queue.add_task(task)
        
        await update.message.reply_text(
            f"✅ Task added!\n**ID:** `{task_id}`\n**Goal:** {goal}",
            parse_mode="Markdown"
        )
    
    async def task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/task <id>`", parse_mode="Markdown")
            return
        
        task = await self.task_queue.get_task(args[0])
        if not task:
            await update.message.reply_text(f"❌ Task not found: `{args[0]}`", parse_mode="Markdown")
            return
        
        await update.message.reply_text(
            f"📋 **Task Details:**\n\n"
            f"**ID:** `{task.task_id}`\n"
            f"**Goal:** {task.goal}\n"
            f"**Status:** {task.status}\n"
            f"**Dependencies:** {', '.join(task.dependencies) or 'None'}\n"
            f"**Created:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.created_at))}",
            parse_mode="Markdown"
        )
    
    async def completetask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/completetask <id>`", parse_mode="Markdown")
            return
        
        success = await self.task_queue.update_task_status(args[0], "COMPLETED", "Completed via Telegram")
        if success:
            await update.message.reply_text(f"✅ Task `{args[0]}` completed!", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Task not found: `{args[0]}`", parse_mode="Markdown")
    
    async def failedtask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/failedtask <id>`", parse_mode="Markdown")
            return
        
        reason = " ".join(args[1:]) if len(args) > 1 else "Failed via Telegram"
        success = await self.task_queue.update_task_status(args[0], "FAILED", reason)
        if success:
            await update.message.reply_text(f"❌ Task `{args[0]}` marked as failed", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Task not found: `{args[0]}`", parse_mode="Markdown")
    
    async def removetask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/removetask <id>`", parse_mode="Markdown")
            return
        
        success = await self.task_queue.remove_task(args[0])
        if success:
            await update.message.reply_text(f"🗑️ Task `{args[0]}` removed", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Task not found: `{args[0]}`", parse_mode="Markdown")
    
    async def cleartasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        count = await self.task_queue.clear_completed()
        await update.message.reply_text(f"🗑️ Cleared {count} completed tasks", parse_mode="Markdown")
    
    # ========================================================================
    # Memory Commands
    # ========================================================================
    
    async def memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /memory command - show memory statistics."""
        if not self._is_allowed(update):
            return
        
        if not self.memory_manager:
            await update.message.reply_text("❌ Memory Manager not initialized")
            return
        
        try:
            stats = self.memory_manager.get_stats()
            
            await update.message.reply_text(
                "🧠 **Memory Statistics:**\n\n"
                "**Session Memory (Fast):**\n"
                f"  • Entries: {stats['session']['total_entries']}\n"
                f"  • Size: {stats['session']['total_size_bytes']} bytes\n\n"
                "**Long-term Memory (Persistent):**\n"
                f"  • Entries: {stats['long_term']['total_entries']}\n"
                f"  • Size: {stats['long_term']['total_size_bytes']} bytes\n\n"
                "**Episodic Memory (Experiences):**\n"
                f"  • Episodes: {stats['episodic']['total_episodes']}\n"
                f"  • Success Rate: {stats['episodic']['success_rate']:.1%}\n\n"
                "**Semantic Memory (Vectors):**\n"
                f"  • Documents: {stats['semantic']['total_documents']}",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Memory error: {str(e)[:100]}")
    
    async def remember_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /remember command - store a memory."""
        if not self._is_allowed(update):
            return
        
        if not self.memory_manager:
            await update.message.reply_text("❌ Memory Manager not initialized")
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: `/remember <key> <value>`\n"
                "Example: `/remember user_name Irfan`",
                parse_mode="Markdown"
            )
            return
        
        key = args[0]
        value = " ".join(args[1:])
        
        # Store in both session and long-term
        await self.memory_manager.remember(key, value, MemoryType.SESSION)
        await self.memory_manager.remember(key, value, MemoryType.LONG_TERM)
        
        await update.message.reply_text(
            f"✅ Remembered!\n**Key:** `{key}`\n**Value:** {value}",
            parse_mode="Markdown"
        )
    
    async def recall_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /recall command - retrieve a memory."""
        if not self._is_allowed(update):
            return
        
        if not self.memory_manager:
            await update.message.reply_text("❌ Memory Manager not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/recall <key>`", parse_mode="Markdown")
            return
        
        key = args[0]
        value = await self.memory_manager.recall_all_tiers(key)
        
        if value is not None:
            await update.message.reply_text(
                f"🧠 **Recalled:**\n**Key:** `{key}`\n**Value:** {value}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ No memory found for key: `{key}`", parse_mode="Markdown")
    
    async def forget_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /forget command - delete a memory."""
        if not self._is_allowed(update):
            return
        
        if not self.memory_manager:
            await update.message.reply_text("❌ Memory Manager not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/forget <key>`", parse_mode="Markdown")
            return
        
        key = args[0]
        deleted = await self.memory_manager.forget(key)
        
        if deleted:
            await update.message.reply_text(f"🗑️ Forgot: `{key}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ No memory found for key: `{key}`", parse_mode="Markdown")
    
    async def searchmemory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /searchmemory command - search across all memory tiers."""
        if not self._is_allowed(update):
            return
        
        if not self.memory_manager:
            await update.message.reply_text("❌ Memory Manager not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/searchmemory <query>`", parse_mode="Markdown")
            return
        
        query = " ".join(args)
        results = await self.memory_manager.search_all(query, limit=5)
        
        lines = [f"🔍 **Search Results for:** `{query}`\n"]
        
        if results['session']:
            lines.append("**Session Memory:**")
            for entry in results['session'][:3]:
                lines.append(f"  • `{entry.key}`: {str(entry.value)[:50]}")
        
        if results['long_term']:
            lines.append("\n**Long-term Memory:**")
            for entry in results['long_term'][:3]:
                lines.append(f"  • `{entry.key}`: {str(entry.value)[:50]}")
        
        if results['semantic']:
            lines.append("\n**Semantic Memory:**")
            for doc in results['semantic'][:3]:
                lines.append(f"  • `{doc['doc_id']}`: {doc['content'][:50]}")
        
        if not any(results.values()):
            lines.append("No results found.")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def logexperience_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /logexperience command - log an experience."""
        if not self._is_allowed(update):
            return
        
        if not self.memory_manager:
            await update.message.reply_text("❌ Memory Manager not initialized")
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: `/logexperience <action> <outcome> [success|fail]`\n"
                "Example: `/logexperience 'Install numpy' 'Success' success`",
                parse_mode="Markdown"
            )
            return
        
        action = args[0]
        outcome = args[1]
        success = len(args) < 3 or args[2].lower() in ['success', 'ok', 'true', 'yes']
        
        episode = await self.memory_manager.log_experience(
            action=action,
            context={"source": "telegram"},
            outcome=outcome,
            success=success,
        )
        
        await update.message.reply_text(
            f"📝 **Experience Logged:**\n"
            f"**ID:** `{episode.episode_id[:8]}`\n"
            f"**Action:** {action}\n"
            f"**Outcome:** {outcome}\n"
            f"**Success:** {'✅' if success else '❌'}",
            parse_mode="Markdown"
        )
    
    async def lessons_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /lessons command - get lessons learned."""
        if not self._is_allowed(update):
            return
        
        if not self.memory_manager:
            await update.message.reply_text("❌ Memory Manager not initialized")
            return
        
        lessons = await self.memory_manager.learn_from_failures()
        
        if not lessons:
            await update.message.reply_text("📚 No lessons learned yet.")
            return
        
        lines = ["📚 **Lessons Learned:**\n"]
        for i, lesson in enumerate(lessons[:10], 1):
            lines.append(f"{i}. {lesson}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    # ========================================================================
    # EventBus Commands
    # ========================================================================
    
    async def events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        history = self.event_bus.get_history(limit=10)
        
        if not history:
            await update.message.reply_text("📭 No events in history")
            return
        
        lines = ["📡 **Recent Events:**\n"]
        for entry in history:
            event = entry["event"]
            ts = time.strftime('%H:%M:%S', time.localtime(entry["published_at"]))
            lines.append(f"• `{ts}` {event.event_type}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    # ========================================================================
    # Adaptive Runtime Commands
    # ========================================================================
    
    async def runtime_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /runtime command - show runtime status."""
        if not self._is_allowed(update):
            return
        
        if not self.runtime:
            await update.message.reply_text("❌ Adaptive Runtime not initialized")
            return
        
        stats = self.runtime.get_stats()
        profile = self.runtime.hardware_profile
        
        lines = ["⚡ **Adaptive Runtime Status**\n"]
        
        if profile:
            lines.append("🖥️ **Hardware:**")
            lines.append(f"  • CPU: {profile.cpu_cores} cores")
            lines.append(f"  • RAM: {profile.total_ram_gb} GB")
            lines.append(f"  • GPU: {'✅ ' + (profile.gpu_model or 'Detected') if profile.has_gpu else '❌ None'}")
            lines.append(f"  • Internet: {'✅' if profile.internet_connected else '❌'}")
            lines.append(f"  • OS: {profile.os_name} {profile.os_version}")
            lines.append("")
        
        lines.append("⚙️ **Runtime:**")
        lines.append(f"  • Mode: `{stats['current_mode']}`")
        lines.append(f"  • Modules: {stats['loaded_module_count']}/{stats['total_module_count']}")
        lines.append(f"  • Mode switches: {stats['mode_switches']}")
        lines.append(f"  • Resource alerts: {stats['resource_alerts']}")
        lines.append(f"  • Uptime: {stats['uptime_seconds']:.0f}s")
        lines.append(f"  • Feasible modes: {', '.join(stats['feasible_modes'])}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def resources_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /resources command - show current resource usage."""
        if not self._is_allowed(update):
            return
        
        if not self.runtime:
            await update.message.reply_text("❌ Adaptive Runtime not initialized")
            return
        
        usage = self.runtime.get_resource_usage()
        
        def threshold_icon(t):
            return {"low": "🟢", "moderate": "🟡", "high": "🟠", "critical": "🔴"}.get(t, "⚪")
        
        lines = ["📊 **Resource Usage**\n"]
        
        cpu = usage["cpu"]
        lines.append(f"{threshold_icon(cpu['threshold'])} **CPU:** {cpu['percent']}% ({cpu['cores']} cores)")
        
        ram = usage["ram"]
        lines.append(f"{threshold_icon(ram['threshold'])} **RAM:** {ram['percent']}% ({ram['used_gb']}/{ram['total_gb']} GB)")
        
        disk = usage["disk"]
        lines.append(f"{threshold_icon(disk['threshold'])} **Disk:** {disk['percent']}% ({disk['used_gb']}/{disk['total_gb']} GB)")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def setmode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /setmode <mode> command - switch operating mode."""
        if not self._is_allowed(update):
            return
        
        if not self.runtime:
            await update.message.reply_text("❌ Adaptive Runtime not initialized")
            return
        
        if not context.args:
            modes = self.runtime.get_feasible_modes()
            await update.message.reply_text(
                f"Usage: `/setmode <mode>`\n\n"
                f"Feasible modes: {', '.join(modes)}",
                parse_mode="Markdown"
            )
            return
        
        new_mode = context.args[0].lower()
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "manual via Telegram"
        
        result = await self.runtime.switch_mode(new_mode, reason=reason)
        
        if result:
            await update.message.reply_text(
                f"✅ Mode switched to `{new_mode}`",
                parse_mode="Markdown"
            )
        else:
            feasible = self.runtime.get_feasible_modes()
            await update.message.reply_text(
                f"❌ Cannot switch to `{new_mode}`\n\n"
                f"Feasible modes: {', '.join(feasible)}",
                parse_mode="Markdown"
            )
    
    async def modules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /modules command - show loaded modules."""
        if not self._is_allowed(update):
            return
        
        if not self.runtime:
            await update.message.reply_text("❌ Adaptive Runtime not initialized")
            return
        
        from orion.core.runtime.runtime import MODULE_PRIORITIES, ModulePriority
        
        loaded = self.runtime.loaded_modules
        
        priority_icons = {
            ModulePriority.CRITICAL: "🔴",
            ModulePriority.HIGH: "🟠",
            ModulePriority.MEDIUM: "🟡",
            ModulePriority.LOW: "🟢",
        }
        
        lines = ["📦 **Modules**\n"]
        for name, priority in sorted(MODULE_PRIORITIES.items(), key=lambda x: x[1].value):
            icon = priority_icons.get(priority, "⚪")
            status = "✅" if name in loaded else "⬜"
            lines.append(f"{status} {icon} `{name}` ({priority.value})")
        
        lines.append(f"\nLoaded: {len(loaded)}/{len(MODULE_PRIORITIES)}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    # ========================================================================
    # Health & Self-Healing Commands
    # ========================================================================
    
    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /health command - show system health."""
        if not self._is_allowed(update):
            return
        
        if not self.health_monitor:
            await update.message.reply_text("❌ Health Monitor not initialized")
            return
        
        report = await self.health_monitor.check_all()
        
        status_icons = {
            "HEALTHY": "🟢",
            "DEGRADED": "🟡",
            "UNHEALTHY": "🔴",
            "CRASHED": "💥",
            "UNKNOWN": "⚪",
        }
        
        lines = [f"{status_icons.get(report.overall_status.value, '⚪')} **System Health: {report.overall_status.value}**\n"]
        
        for svc in report.services:
            icon = status_icons.get(svc.status.value, '⚪')
            lines.append(f"{icon} `{svc.service_name}`: {svc.status.value}")
        
        lines.append(f"\n📊 CPU: {report.cpu_percent}% | RAM: {report.ram_percent}% | Disk: {report.disk_percent}%")
        lines.append(f"✅ Passed: {report.checks_passed} | ❌ Failed: {report.checks_failed}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def healer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /healer command - show self-healer status."""
        if not self._is_allowed(update):
            return
        
        if not self.self_healer:
            await update.message.reply_text("❌ Self-Healer not initialized")
            return
        
        stats = self.self_healer.get_stats()
        
        lines = ["🛡️ **Self-Healer Status**\n"]
        lines.append(f"• Running: {'✅' if stats['running'] else '❌'}")
        lines.append(f"• Total recoveries: {stats['total_recoveries']}")
        lines.append(f"• Successful: {stats['successful_recoveries']}")
        lines.append(f"• Failed: {stats['failed_recoveries']}")
        lines.append(f"• Success rate: {stats['success_rate']}%")
        lines.append(f"• Max attempts: {stats['max_attempts']}")
        
        # Show recent history
        history = self.self_healer.get_recovery_history(5)
        if history:
            lines.append("\n📋 **Recent Recoveries:**")
            for r in history:
                lines.append(f"  • {r['service_name']}: {r['action_taken']} ({'✅' if r['success'] else '❌'})")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    # ========================================================================
    # Message Handler (with Tool Calling)
    # ========================================================================
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update):
            return
        
        user = update.effective_user
        message_text = update.message.text
        user_id = user.id
        
        logger.info("Message from %s: %s", user.first_name, message_text[:50])
        
        # Publish event to EventBus
        await self.event_bus.publish(Event(
            event_type="telegram.message",
            payload={
                "user_id": user_id,
                "username": user.username,
                "first_name": user.first_name,
                "message": message_text,
                "chat_id": update.effective_chat.id,
                "message_id": update.message.message_id,
            },
            timestamp=time.time(),
            source="telegram_bot",
        ))
        
        # If LLM is available, think and respond with tools
        if self.llm_client:
            try:
                # Show typing indicator
                await update.message.chat.send_action("typing")
                
                # Get or create conversation history
                if user_id not in self._conversation_history:
                    self._conversation_history[user_id] = []
                
                history = self._conversation_history[user_id]
                
                # Add user message to history
                history.append({"role": "user", "content": message_text})
                
                # Trim history if too long
                if len(history) > self._max_history:
                    history = history[-self._max_history:]
                    self._conversation_history[user_id] = history
                
                # Call LLM with tools
                response = await self.llm_client.chat_with_tools(
                    prompt=message_text,
                    tools=self._tools,
                    system=self._system_prompt,
                    model="mimo-v2.5-pro",
                )
                
                # Check if LLM wants to use tools
                raw = response.raw or {}
                choice = raw.get("choices", [{}])[0]
                message = choice.get("message", {})
                tool_calls = message.get("tool_calls", [])
                
                if tool_calls:
                    # Execute tools and get results
                    tool_results = []
                    for call in tool_calls:
                        func = call.get("function", {})
                        tool_name = func.get("name", "")
                        args_str = func.get("arguments", "{}")
                        
                        try:
                            arguments = json.loads(args_str) if args_str else {}
                        except:
                            arguments = {}
                        
                        # Show typing while executing
                        await update.message.chat.send_action("typing")
                        
                        # Execute the tool
                        result = await self._execute_tool(tool_name, arguments)
                        tool_results.append({"tool": tool_name, "result": result})
                        
                        logger.info("Tool executed: %s", tool_name)
                    
                    # Build tool results message for LLM
                    tool_msg = "Tool results:\n"
                    for tr in tool_results:
                        tool_msg += f"\n### {tr['tool']}:\n{tr['result']}\n"
                    
                    # Add tool results to history
                    history.append({"role": "assistant", "content": "I used tools to get information."})
                    history.append({"role": "user", "content": f"Tool results:\n{tool_msg}\n\nNow respond to the user's original message using this information."})
                    
                    # Get final response from LLM
                    await update.message.chat.send_action("typing")
                    final_response = await self.llm_client.chat(
                        prompt=f"Tool results:\n{tool_msg}\n\nUser asked: {message_text}\n\nRespond naturally using the tool results.",
                        system=self._system_prompt,
                        model="mimo-v2.5-pro",
                    )
                    
                    assistant_response = final_response.content
                    
                    # Add to history
                    history.append({"role": "assistant", "content": assistant_response})
                else:
                    # No tool calls, just respond
                    assistant_response = message.get("content", response.content)
                    
                    # Add to history
                    history.append({"role": "assistant", "content": assistant_response})
                
                self._conversation_history[user_id] = history
                
                # Send response
                if len(assistant_response) > 4000:
                    chunks = [assistant_response[i:i+4000] for i in range(0, len(assistant_response), 4000)]
                    for chunk in chunks:
                        await update.message.reply_text(chunk, parse_mode="Markdown")
                else:
                    await update.message.reply_text(assistant_response, parse_mode="Markdown")
                
                logger.info("LLM response: model=%s tokens=%d/%d", 
                          response.model, response.tokens_input, response.tokens_output)
            
            except Exception as e:
                logger.error("LLM error: %s", e)
                await update.message.reply_text(
                    f"⚠️ Thinking error: {str(e)[:100]}\n\nUse /help to see commands.",
                    parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                f"📨 Received: _{message_text}_\n\n🤖 LLM not connected. Use /help to see commands.",
                parse_mode="Markdown"
            )
    
    # ========================================================================
    # Response Handler
    # ========================================================================
    
    async def handle_response(self, event: Event) -> None:
        if event.event_type == "telegram.response":
            chat_id = event.payload.get("chat_id")
            message = event.payload.get("message", "")
            
            if chat_id and message and self.app:
                await self.app.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    
    def _is_allowed(self, update: Update) -> bool:
        user_id = update.effective_user.id
        if user_id != self.allowed_user_id:
            logger.warning("Unauthorized access attempt from user %d", user_id)
            return False
        return True
    
    async def post_init(self, application: Application) -> None:
        await self.event_bus.subscribe("telegram.response", self.handle_response)
        logger.info("Telegram bot subscribed to 'telegram.response' events")
    
    async def post_shutdown(self, application: Application) -> None:
        await self.event_bus.unsubscribe("telegram.response", self.handle_response)
        if self.task_queue:
            await self.task_queue.stop()
        if self.memory_manager:
            await self.memory_manager.stop()
        logger.info("Telegram bot shutdown complete")
    
    def run(self) -> None:
        logger.info("Starting Telegram bot...")
        
        self.app = (
            Application.builder()
            .token(self.token)
            .post_init(self.post_init)
            .post_shutdown(self.post_shutdown)
            .build()
        )
        
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("ping", self.ping_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        
        # State Machine commands
        self.app.add_handler(CommandHandler("state", self.state_command))
        self.app.add_handler(CommandHandler("transitions", self.transitions_command))
        self.app.add_handler(CommandHandler("setstate", self.setstate_command))
        
        # Task Queue commands
        self.app.add_handler(CommandHandler("tasks", self.tasks_command))
        self.app.add_handler(CommandHandler("addtask", self.addtask_command))
        self.app.add_handler(CommandHandler("task", self.task_command))
        self.app.add_handler(CommandHandler("completetask", self.completetask_command))
        self.app.add_handler(CommandHandler("failedtask", self.failedtask_command))
        self.app.add_handler(CommandHandler("removetask", self.removetask_command))
        self.app.add_handler(CommandHandler("cleartasks", self.cleartasks_command))
        
        # Memory commands
        self.app.add_handler(CommandHandler("memory", self.memory_command))
        self.app.add_handler(CommandHandler("remember", self.remember_command))
        self.app.add_handler(CommandHandler("recall", self.recall_command))
        self.app.add_handler(CommandHandler("forget", self.forget_command))
        self.app.add_handler(CommandHandler("searchmemory", self.searchmemory_command))
        self.app.add_handler(CommandHandler("logexperience", self.logexperience_command))
        self.app.add_handler(CommandHandler("lessons", self.lessons_command))
        
        # EventBus commands
        self.app.add_handler(CommandHandler("events", self.events_command))
        
        # Adaptive Runtime commands
        self.app.add_handler(CommandHandler("runtime", self.runtime_command))
        self.app.add_handler(CommandHandler("resources", self.resources_command))
        self.app.add_handler(CommandHandler("setmode", self.setmode_command))
        self.app.add_handler(CommandHandler("modules", self.modules_command))
        
        # Health & Self-Healing commands
        self.app.add_handler(CommandHandler("health", self.health_command))
        self.app.add_handler(CommandHandler("healer", self.healer_command))
        
        # Message handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Telegram bot is running! Press Ctrl+C to stop.")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    BOT_TOKEN = "8969014252:AAFr0E3qEATdBY4TYb0fL8lhsTEClWdYoyo"
    ALLOWED_USER_ID = 7429947930
    
    # Initialize components
    event_bus = get_event_bus()
    state_machine = StateMachine(event_bus, initial_state=State.IDLE)
    task_queue = TaskQueueEngine(event_bus, state_file="state/task_queue.json")
    memory_manager = MemoryManager(event_bus)
    runtime = AdaptiveRuntime(event_bus)
    
    # Initialize LLM Client (mimo-v2.5-pro via OpenRouter)
    llm_client = LLMClient(
        event_bus=event_bus,
        default_model="mimo-v2.5-pro",
    )
    
    bot = OrionTelegramBot(
        token=BOT_TOKEN,
        allowed_user_id=ALLOWED_USER_ID,
        event_bus=event_bus,
        state_machine=state_machine,
        task_queue=task_queue,
        memory_manager=memory_manager,
        runtime=runtime,
        llm_client=llm_client,
    )
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
