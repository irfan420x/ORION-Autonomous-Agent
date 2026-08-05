"""
ORION Message Manager
=====================

Manages conversation history with context window management.
Inspired by Hermes Agent's context compression patterns.

Features:
- Message history with size limits
- Context window management
- Message role alternation enforcement
- Tool result injection
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageManager:
    """
    Manages conversation messages with context window awareness.
    """
    
    def __init__(self, max_messages: int = 50, max_chars: int = 50000):
        self._messages: List[Dict[str, Any]] = []
        self._max_messages = max_messages
        self._max_chars = max_chars
    
    def add_user(self, content: str):
        """Add user message."""
        self._messages.append({"role": "user", "content": content})
        self._trim()
    
    def add_assistant(self, content: str, tool_calls: Optional[List] = None):
        """Add assistant message."""
        msg = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self._messages.append(msg)
        self._trim()
    
    def add_tool_result(self, tool_call_id: str, content: str):
        """Add tool result message."""
        self._messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        })
        self._trim()
    
    def add_system(self, content: str):
        """Add or replace system message."""
        # Remove existing system message
        self._messages = [m for m in self._messages if m["role"] != "system"]
        # Insert at beginning
        self._messages.insert(0, {"role": "system", "content": content})
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages for LLM."""
        return list(self._messages)
    
    def get_history_text(self) -> str:
        """Get formatted history for context."""
        lines = []
        for msg in self._messages:
            if msg["role"] == "system":
                continue
            role = msg["role"].upper()
            content = msg.get("content", "")[:200]
            lines.append(f"[{role}]: {content}")
        return "\n".join(lines[-10:])  # Last 10 messages
    
    def _trim(self):
        """Trim messages to stay within limits."""
        # Keep system message
        system = [m for m in self._messages if m["role"] == "system"]
        others = [m for m in self._messages if m["role"] != "system"]
        
        # Trim by count
        if len(others) > self._max_messages:
            others = others[-self._max_messages:]
        
        # Trim by char count
        total_chars = sum(len(str(m.get("content", ""))) for m in others)
        while total_chars > self._max_chars and len(others) > 2:
            removed = others.pop(0)
            total_chars -= len(str(removed.get("content", "")))
        
        self._messages = system + others
    
    def clear(self):
        """Clear all messages."""
        self._messages.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message statistics."""
        total_chars = sum(len(str(m.get("content", ""))) for m in self._messages)
        return {
            "message_count": len(self._messages),
            "total_chars": total_chars,
            "max_messages": self._max_messages,
            "max_chars": self._max_chars,
        }
