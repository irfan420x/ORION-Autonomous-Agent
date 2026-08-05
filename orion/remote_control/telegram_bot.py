"""
ORION Telegram Bot Integration
=============================

Telegram bot that connects to ORION's EventBus, StateMachine, and TaskQueue.

Usage:
    python -m orion.remote_control.telegram_bot
"""

import asyncio
import logging
import time
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from orion.contracts.agent_contracts import Event, Task
from orion.core.communication.event_bus import EventBus, get_event_bus
from orion.core.state.state_machine import StateMachine, State
from orion.core.state.task_queue import TaskQueueEngine

logger = logging.getLogger(__name__)


class OrionTelegramBot:
    """
    Telegram bot integration for ORION.
    
    Connects Telegram messages to ORION's EventBus, StateMachine, and TaskQueue.
    """
    
    def __init__(
        self,
        token: str,
        allowed_user_id: int,
        event_bus: Optional[EventBus] = None,
        state_machine: Optional[StateMachine] = None,
        task_queue: Optional[TaskQueueEngine] = None,
    ):
        """
        Initialize the Telegram bot.
        
        Args:
            token: Bot token from @BotFather
            allowed_user_id: Telegram user ID allowed to interact
            event_bus: Optional EventBus instance
            state_machine: Optional StateMachine instance
            task_queue: Optional TaskQueueEngine instance
        """
        self.token = token
        self.allowed_user_id = allowed_user_id
        self.event_bus = event_bus or get_event_bus()
        self.state_machine = state_machine
        self.task_queue = task_queue
        self.app: Optional[Application] = None
        
        logger.info("OrionTelegramBot initialized for user %d", allowed_user_id)
    
    # ========================================================================
    # Basic Commands
    # ========================================================================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        if not self._is_allowed(update):
            return
        
        await update.message.reply_text(
            "🤖 **ORION Autonomous Agent**\n\n"
            "I am ORION, your AI assistant.\n\n"
            "📋 **Available Commands:**\n"
            "/help - Show all commands\n"
            "/status - System status\n"
            "/ping - Test connection\n\n"
            "🔄 **State Machine:**\n"
            "/state - Current state\n"
            "/transitions - Valid transitions\n"
            "/setstate <state> - Change state\n\n"
            "📝 **Task Queue:**\n"
            "/tasks - List all tasks\n"
            "/addtask <goal> - Add new task\n"
            "/task <id> - Get task details\n"
            "/completetask <id> - Mark task complete\n"
            "/failedtask <id> - Mark task failed\n"
            "/cleartasks - Clear completed tasks\n",
            parse_mode="Markdown"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        if not self._is_allowed(update):
            return
        
        await update.message.reply_text(
            "📋 **All Commands:**\n\n"
            "**Basic:**\n"
            "/start - Welcome message\n"
            "/help - This help\n"
            "/status - Full system status\n"
            "/ping - Test connection\n\n"
            "**State Machine:**\n"
            "/state - Current state\n"
            "/transitions - Valid transitions\n"
            "/setstate <state> - Change state\n"
            "  States: IDLE, PROCESSING, PAUSED, ERROR, SHUTDOWN\n\n"
            "**Task Queue:**\n"
            "/tasks - List all tasks\n"
            "/tasks pending - Pending tasks only\n"
            "/tasks completed - Completed tasks only\n"
            "/addtask <goal> - Add new task\n"
            "/task <id> - Get task details\n"
            "/completetask <id> - Mark task complete\n"
            "/failedtask <id> - Mark task failed\n"
            "/removetask <id> - Remove task\n"
            "/cleartasks - Clear completed tasks\n\n"
            "**EventBus:**\n"
            "/events - Recent events\n"
            "/stats - System statistics\n",
            parse_mode="Markdown"
        )
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /ping command."""
        if not self._is_allowed(update):
            return
        
        start_time = time.time()
        msg = await update.message.reply_text("🏓 Pong!")
        elapsed = (time.time() - start_time) * 1000
        await msg.edit_text(f"🏓 Pong! ({elapsed:.0f}ms)")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command - full system status."""
        if not self._is_allowed(update):
            return
        
        lines = ["📊 **ORION System Status**\n"]
        
        # State Machine status
        if self.state_machine:
            sm_stats = self.state_machine.get_stats()
            lines.append("🔄 **State Machine:**")
            lines.append(f"  • Current: `{sm_stats['current_state']}`")
            lines.append(f"  • Transitions: {sm_stats['total_transitions']}")
            lines.append(f"  • Valid next: {', '.join(sm_stats['valid_transitions']) or 'None'}")
            lines.append("")
        
        # Task Queue status
        if self.task_queue:
            tq_stats = self.task_queue.get_stats()
            lines.append("📝 **Task Queue:**")
            lines.append(f"  • Total: {tq_stats['total_tasks']}")
            for status, count in tq_stats.get('status_counts', {}).items():
                lines.append(f"  • {status}: {count}")
            lines.append(f"  • Completed (all time): {tq_stats['total_completed']}")
            lines.append(f"  • Failed (all time): {tq_stats['total_failed']}")
            lines.append("")
        
        # EventBus status
        eb_stats = self.event_bus.get_stats()
        lines.append("📡 **EventBus:**")
        lines.append(f"  • Published: {eb_stats['total_published']}")
        lines.append(f"  • Delivered: {eb_stats['total_delivered']}")
        lines.append(f"  • Errors: {eb_stats['total_errors']}")
        lines.append(f"  • Subscriptions: {eb_stats['active_subscriptions']}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command."""
        if not self._is_allowed(update):
            return
        
        eb_stats = self.event_bus.get_stats()
        
        await update.message.reply_text(
            "📈 **EventBus Statistics:**\n\n"
            f"• Total Published: {eb_stats['total_published']}\n"
            f"• Total Delivered: {eb_stats['total_delivered']}\n"
            f"• Total Errors: {eb_stats['total_errors']}\n"
            f"• Active Subscriptions: {eb_stats['active_subscriptions']}\n"
            f"• Unique Patterns: {eb_stats['unique_patterns']}\n"
            f"• History Size: {eb_stats['history_size']}",
            parse_mode="Markdown"
        )
    
    # ========================================================================
    # State Machine Commands
    # ========================================================================
    
    async def state_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /state command - show current state."""
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
        """Handle /transitions command - show valid transitions."""
        if not self._is_allowed(update):
            return
        
        if not self.state_machine:
            await update.message.reply_text("❌ State Machine not initialized")
            return
        
        current = self.state_machine.current_state
        valid = self.state_machine.get_valid_transitions()
        
        # Show all possible transitions
        all_transitions = StateMachine.VALID_TRANSITIONS
        
        lines = ["🔄 **State Transitions:**\n"]
        for state, targets in all_transitions.items():
            marker = " ← **current**" if state == current else ""
            targets_str = ", ".join(f"`{t.value}`" for t in targets) or "None"
            lines.append(f"• `{state.value}`{marker} → {targets_str}")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def setstate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /setstate command - change state."""
        if not self._is_allowed(update):
            return
        
        if not self.state_machine:
            await update.message.reply_text("❌ State Machine not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text(
                "Usage: `/setstate <state>`\n"
                "States: IDLE, PROCESSING, PAUSED, ERROR, SHUTDOWN",
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
                f"✅ State changed to `{new_state.value}`\n"
                f"Reason: {reason}",
                parse_mode="Markdown"
            )
        else:
            valid = self.state_machine.get_valid_transitions()
            await update.message.reply_text(
                f"❌ Invalid transition: `{self.state_machine.current_state.value}` → `{new_state.value}`\n\n"
                f"Valid transitions: {', '.join(f'`{s.value}`' for s in valid)}",
                parse_mode="Markdown"
            )
    
    # ========================================================================
    # Task Queue Commands
    # ========================================================================
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /tasks command - list tasks."""
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
        for task in tasks[:20]:  # Limit to 20
            status_emoji = {
                "PENDING": "⏳",
                "IN_PROGRESS": "🔄",
                "COMPLETED": "✅",
                "FAILED": "❌",
                "CANCELLED": "🚫",
            }.get(task.status, "❓")
            
            lines.append(f"{status_emoji} `{task.task_id}` - {task.goal[:50]}")
        
        if len(tasks) > 20:
            lines.append(f"\n... and {len(tasks) - 20} more")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    async def addtask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /addtask command - add a new task."""
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text(
                "Usage: `/addtask <goal>`\n"
                "Example: `/addtask Research AI agents`",
                parse_mode="Markdown"
            )
            return
        
        goal = " ".join(args)
        task_id = f"task_{int(time.time())}"
        
        task = Task(
            task_id=task_id,
            goal=goal,
            status="PENDING",
            dependencies=[],
            created_at=time.time(),
            updated_at=time.time(),
        )
        
        await self.task_queue.add_task(task)
        
        await update.message.reply_text(
            f"✅ Task added!\n\n"
            f"**ID:** `{task_id}`\n"
            f"**Goal:** {goal}",
            parse_mode="Markdown"
        )
    
    async def task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /task command - get task details."""
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/task <id>`", parse_mode="Markdown")
            return
        
        task_id = args[0]
        task = await self.task_queue.get_task(task_id)
        
        if not task:
            await update.message.reply_text(f"❌ Task not found: `{task_id}`", parse_mode="Markdown")
            return
        
        await update.message.reply_text(
            f"📋 **Task Details:**\n\n"
            f"**ID:** `{task.task_id}`\n"
            f"**Goal:** {task.goal}\n"
            f"**Status:** {task.status}\n"
            f"**Dependencies:** {', '.join(task.dependencies) or 'None'}\n"
            f"**Assigned:** {task.assigned_agent or 'Unassigned'}\n"
            f"**Created:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.created_at))}\n"
            f"**Updated:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.updated_at))}",
            parse_mode="Markdown"
        )
    
    async def completetask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /completetask command."""
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/completetask <id>`", parse_mode="Markdown")
            return
        
        task_id = args[0]
        success = await self.task_queue.update_task_status(task_id, "COMPLETED", "Completed via Telegram")
        
        if success:
            await update.message.reply_text(f"✅ Task `{task_id}` marked as completed!", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Task not found: `{task_id}`", parse_mode="Markdown")
    
    async def failedtask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /failedtask command."""
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/failedtask <id>`", parse_mode="Markdown")
            return
        
        task_id = args[0]
        reason = " ".join(args[1:]) if len(args) > 1 else "Failed via Telegram"
        success = await self.task_queue.update_task_status(task_id, "FAILED", reason)
        
        if success:
            await update.message.reply_text(f"❌ Task `{task_id}` marked as failed", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Task not found: `{task_id}`", parse_mode="Markdown")
    
    async def removetask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /removetask command."""
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/removetask <id>`", parse_mode="Markdown")
            return
        
        task_id = args[0]
        success = await self.task_queue.remove_task(task_id)
        
        if success:
            await update.message.reply_text(f"🗑️ Task `{task_id}` removed", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Task not found: `{task_id}`", parse_mode="Markdown")
    
    async def cleartasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cleartasks command."""
        if not self._is_allowed(update):
            return
        
        if not self.task_queue:
            await update.message.reply_text("❌ Task Queue not initialized")
            return
        
        count = await self.task_queue.clear_completed()
        await update.message.reply_text(f"🗑️ Cleared {count} completed tasks", parse_mode="Markdown")
    
    # ========================================================================
    # EventBus Commands
    # ========================================================================
    
    async def events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /events command - show recent events."""
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
    # Message Handler
    # ========================================================================
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages."""
        if not self._is_allowed(update):
            return
        
        user = update.effective_user
        message_text = update.message.text
        
        logger.info("Message from %s: %s", user.first_name, message_text[:50])
        
        # Publish message to EventBus
        await self.event_bus.publish(Event(
            event_type="telegram.message",
            payload={
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "message": message_text,
                "chat_id": update.effective_chat.id,
                "message_id": update.message.message_id,
            },
            timestamp=time.time(),
            source="telegram_bot",
        ))
        
        # Simple echo response
        await update.message.reply_text(
            f"📨 Received: _{message_text}_\n\n"
            "Use /help to see available commands.",
            parse_mode="Markdown"
        )
    
    # ========================================================================
    # Response Handler (for AI engine)
    # ========================================================================
    
    async def handle_response(self, event: Event) -> None:
        """Handle response events from ORION's AI engine."""
        if event.event_type == "telegram.response":
            chat_id = event.payload.get("chat_id")
            message = event.payload.get("message", "")
            
            if chat_id and message and self.app:
                await self.app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
    
    def _is_allowed(self, update: Update) -> bool:
        """Check if the user is allowed to interact."""
        user_id = update.effective_user.id
        if user_id != self.allowed_user_id:
            logger.warning("Unauthorized access attempt from user %d", user_id)
            return False
        return True
    
    async def post_init(self, application: Application) -> None:
        """Called after application initialization."""
        await self.event_bus.subscribe("telegram.response", self.handle_response)
        logger.info("Telegram bot subscribed to 'telegram.response' events")
    
    async def post_shutdown(self, application: Application) -> None:
        """Called before shutdown."""
        await self.event_bus.unsubscribe("telegram.response", self.handle_response)
        
        # Persist task queue
        if self.task_queue:
            await self.task_queue.stop()
        
        logger.info("Telegram bot shutdown complete")
    
    def run(self) -> None:
        """Start the Telegram bot."""
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
        
        # EventBus commands
        self.app.add_handler(CommandHandler("events", self.events_command))
        
        # Message handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Telegram bot is running! Press Ctrl+C to stop.")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point."""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Bot configuration
    BOT_TOKEN = "8969014252:AAFr0E3qEATdBY4TYb0fL8lhsTEClWdYoyo"
    ALLOWED_USER_ID = 7429947930
    
    # Initialize components
    event_bus = get_event_bus()
    state_machine = StateMachine(event_bus, initial_state=State.IDLE)
    task_queue = TaskQueueEngine(event_bus, state_file="state/task_queue.json")
    
    # Create bot with all components
    bot = OrionTelegramBot(
        token=BOT_TOKEN,
        allowed_user_id=ALLOWED_USER_ID,
        event_bus=event_bus,
        state_machine=state_machine,
        task_queue=task_queue,
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
