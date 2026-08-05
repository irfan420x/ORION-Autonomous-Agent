"""
ORION Permission Model
======================

User-controlled permission system for all tool access.
Inspired by Claude Code's multi-layer permission architecture.

Permission Levels:
- ALLOW: Execute immediately, no confirmation
- ALLOW_ONCE: Allow this single execution only
- ALLOW_SESSION: Allow for current session
- CONFIRM_USER: Ask user before executing
- DENY: Completely blocked

Features:
- Per-tool permission rules
- Per-user permission overrides
- Session-level permissions
- Audit logging
- Integration with EventBus

Usage:
    pm = PermissionManager(event_bus)
    pm.set_rule("shell_execute", PermissionLevel.ALLOW)
    result = pm.check("shell_execute", user_id=123)
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """Permission levels for tool access."""
    ALLOW = "ALLOW"                    # Execute immediately
    ALLOW_ONCE = "ALLOW_ONCE"          # Allow this single execution
    ALLOW_SESSION = "ALLOW_SESSION"    # Allow for current session
    CONFIRM_USER = "CONFIRM_USER"      # Ask user before executing
    DENY = "DENY"                      # Completely blocked


class PermissionDecision(str, Enum):
    """Result of a permission check."""
    GRANTED = "granted"
    DENIED = "denied"
    NEEDS_CONFIRMATION = "needs_confirmation"


class AuditEntry:
    """A single audit log entry."""
    
    def __init__(
        self,
        tool_name: str,
        user_id: Optional[int],
        decision: PermissionDecision,
        timestamp: float,
        details: Optional[str] = None,
    ):
        self.tool_name = tool_name
        self.user_id = user_id
        self.decision = decision
        self.timestamp = timestamp
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "user_id": self.user_id,
            "decision": self.decision.value,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class PermissionManager:
    """
    User-controlled permission system for ORION tools.
    """
    
    # Default permission rules
    DEFAULT_RULES: Dict[str, PermissionLevel] = {
        # System info - always allow
        "get_system_info": PermissionLevel.ALLOW,
        "get_health_status": PermissionLevel.ALLOW,
        "get_runtime_status": PermissionLevel.ALLOW,
        "get_time_date": PermissionLevel.ALLOW,
        
        # Memory - allow
        "remember": PermissionLevel.ALLOW,
        "recall": PermissionLevel.ALLOW,
        "search_memory": PermissionLevel.ALLOW,
        
        # Tasks - allow
        "add_task": PermissionLevel.ALLOW,
        "list_tasks": PermissionLevel.ALLOW,
        
        # File operations - confirm
        "create_file": PermissionLevel.CONFIRM_USER,
        "run_shell_command": PermissionLevel.CONFIRM_USER,
        
        # Dangerous - deny by default
        "delete_file": PermissionLevel.CONFIRM_USER,
        "kill_process": PermissionLevel.DENY,
    }
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self._event_bus = event_bus
        
        # Permission rules: tool_name -> PermissionLevel
        self._rules: Dict[str, PermissionLevel] = dict(self.DEFAULT_RULES)
        
        # User-specific overrides: (user_id, tool_name) -> PermissionLevel
        self._user_overrides: Dict[tuple, PermissionLevel] = {}
        
        # Session permissions: (session_id, tool_name) -> PermissionLevel
        self._session_permissions: Dict[tuple, PermissionLevel] = {}
        
        # One-time allowances: set of (user_id, tool_name)
        self._once_allowances: Set[tuple] = set()
        
        # Audit log
        self._audit_log: List[AuditEntry] = []
        self._max_audit_log: int = 1000
        
        # Stats
        self._total_checks: int = 0
        self._total_granted: int = 0
        self._total_denied: int = 0
        self._total_confirmations: int = 0
        
        logger.info("PermissionManager initialized with %d default rules", len(self.DEFAULT_RULES))
    
    # ── Rule Management ───────────────────────────────────────
    
    def set_rule(self, tool_name: str, level: PermissionLevel) -> None:
        """Set a permission rule for a tool."""
        self._rules[tool_name] = level
        logger.info("Permission rule set: %s -> %s", tool_name, level.value)
        
        if self._event_bus:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._event_bus.publish(Event(
                    event_type="permission.rule_changed",
                    payload={"tool_name": tool_name, "level": level.value},
                    timestamp=time.time(),
                    source="permission_manager",
                )))
            except RuntimeError:
                # No event loop running, skip event publishing
                pass
    
    def get_rule(self, tool_name: str) -> PermissionLevel:
        """Get the permission rule for a tool."""
        return self._rules.get(tool_name, PermissionLevel.CONFIRM_USER)
    
    def set_user_override(self, user_id: int, tool_name: str, level: PermissionLevel) -> None:
        """Set a user-specific permission override."""
        self._user_overrides[(user_id, tool_name)] = level
        logger.info("User override set: user=%d tool=%s -> %s", user_id, tool_name, level.value)
    
    def set_session_permission(self, session_id: str, tool_name: str, level: PermissionLevel) -> None:
        """Set a session-level permission."""
        self._session_permissions[(session_id, tool_name)] = level
    
    def allow_once(self, user_id: int, tool_name: str) -> None:
        """Allow a single execution for a user."""
        self._once_allowances.add((user_id, tool_name))
    
    # ── Permission Check ──────────────────────────────────────
    
    def check(
        self,
        tool_name: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> PermissionDecision:
        """
        Check if a tool execution is permitted.
        
        Priority order:
        1. One-time allowance
        2. Session permission
        3. User override
        4. Global rule
        """
        self._total_checks += 1
        
        # 1. Check one-time allowance
        if user_id and (user_id, tool_name) in self._once_allowances:
            self._once_allowances.discard((user_id, tool_name))
            self._record_audit(tool_name, user_id, PermissionDecision.GRANTED, "one-time allowance")
            self._total_granted += 1
            return PermissionDecision.GRANTED
        
        # 2. Check session permission
        if session_id and (session_id, tool_name) in self._session_permissions:
            level = self._session_permissions[(session_id, tool_name)]
            decision = self._level_to_decision(level)
            self._record_audit(tool_name, user_id, decision, "session permission")
            self._update_stats(decision)
            return decision
        
        # 3. Check user override
        if user_id and (user_id, tool_name) in self._user_overrides:
            level = self._user_overrides[(user_id, tool_name)]
            decision = self._level_to_decision(level)
            self._record_audit(tool_name, user_id, decision, "user override")
            self._update_stats(decision)
            return decision
        
        # 4. Check global rule
        level = self._rules.get(tool_name, PermissionLevel.CONFIRM_USER)
        decision = self._level_to_decision(level)
        self._record_audit(tool_name, user_id, decision, "global rule")
        self._update_stats(decision)
        return decision
    
    def _level_to_decision(self, level: PermissionLevel) -> PermissionDecision:
        """Convert permission level to decision."""
        if level == PermissionLevel.ALLOW:
            return PermissionDecision.GRANTED
        elif level == PermissionLevel.ALLOW_ONCE:
            return PermissionDecision.GRANTED
        elif level == PermissionLevel.ALLOW_SESSION:
            return PermissionDecision.GRANTED
        elif level == PermissionLevel.CONFIRM_USER:
            return PermissionDecision.NEEDS_CONFIRMATION
        elif level == PermissionLevel.DENY:
            return PermissionDecision.DENIED
        return PermissionDecision.DENIED
    
    def _update_stats(self, decision: PermissionDecision) -> None:
        """Update statistics."""
        if decision == PermissionDecision.GRANTED:
            self._total_granted += 1
        elif decision == PermissionDecision.DENIED:
            self._total_denied += 1
        elif decision == PermissionDecision.NEEDS_CONFIRMATION:
            self._total_confirmations += 1
    
    # ── Audit Logging ─────────────────────────────────────────
    
    def _record_audit(
        self,
        tool_name: str,
        user_id: Optional[int],
        decision: PermissionDecision,
        details: Optional[str] = None,
    ) -> None:
        """Record an audit log entry."""
        entry = AuditEntry(
            tool_name=tool_name,
            user_id=user_id,
            decision=decision,
            timestamp=time.time(),
            details=details,
        )
        self._audit_log.append(entry)
        
        # Trim if too long
        if len(self._audit_log) > self._max_audit_log:
            self._audit_log = self._audit_log[-self._max_audit_log:]
    
    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return [e.to_dict() for e in self._audit_log[-limit:]]
    
    # ── Statistics ────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """Get permission manager statistics."""
        return {
            "total_rules": len(self._rules),
            "user_overrides": len(self._user_overrides),
            "session_permissions": len(self._session_permissions),
            "once_allowances": len(self._once_allowances),
            "total_checks": self._total_checks,
            "total_granted": self._total_granted,
            "total_denied": self._total_denied,
            "total_confirmations": self._total_confirmations,
            "audit_log_size": len(self._audit_log),
        }
    
    def get_rules(self) -> Dict[str, str]:
        """Get all permission rules."""
        return {k: v.value for k, v in self._rules.items()}
