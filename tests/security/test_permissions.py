"""
Tests for ORION Permission Model (M4.4)
========================================
"""

import asyncio
import pytest
import time

from orion.core.communication.event_bus import EventBus
from orion.security.permission_manager import (
    PermissionManager, PermissionLevel, PermissionDecision,
    AuditEntry,
)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def pm(event_bus):
    return PermissionManager(event_bus)


# ── PermissionLevel Tests ────────────────────────────────────

class TestPermissionLevel:
    def test_all_levels(self):
        assert PermissionLevel.ALLOW == "ALLOW"
        assert PermissionLevel.ALLOW_ONCE == "ALLOW_ONCE"
        assert PermissionLevel.ALLOW_SESSION == "ALLOW_SESSION"
        assert PermissionLevel.CONFIRM_USER == "CONFIRM_USER"
        assert PermissionLevel.DENY == "DENY"


class TestPermissionDecision:
    def test_all_decisions(self):
        assert PermissionDecision.GRANTED == "granted"
        assert PermissionDecision.DENIED == "denied"
        assert PermissionDecision.NEEDS_CONFIRMATION == "needs_confirmation"


# ── PermissionManager Tests ──────────────────────────────────

class TestPermissionManager:
    def test_initial_state(self, pm):
        stats = pm.get_stats()
        assert stats["total_checks"] == 0
        assert stats["total_rules"] > 0

    def test_default_rules(self, pm):
        rules = pm.get_rules()
        assert "get_system_info" in rules
        assert rules["get_system_info"] == "ALLOW"
        assert "run_shell_command" in rules
        assert rules["run_shell_command"] == "CONFIRM_USER"

    def test_set_rule(self, pm):
        pm.set_rule("my_tool", PermissionLevel.ALLOW)
        assert pm.get_rule("my_tool") == PermissionLevel.ALLOW

    def test_get_rule_default(self, pm):
        """Unknown tools default to CONFIRM_USER."""
        assert pm.get_rule("unknown_tool") == PermissionLevel.CONFIRM_USER

    def test_check_allow(self, pm):
        """ALLOW tools should be granted."""
        decision = pm.check("get_system_info", user_id=123)
        assert decision == PermissionDecision.GRANTED

    def test_check_deny(self, pm):
        """DENY tools should be denied."""
        pm.set_rule("dangerous_tool", PermissionLevel.DENY)
        decision = pm.check("dangerous_tool", user_id=123)
        assert decision == PermissionDecision.DENIED

    def test_check_confirm(self, pm):
        """CONFIRM_USER tools should need confirmation."""
        decision = pm.check("run_shell_command", user_id=123)
        assert decision == PermissionDecision.NEEDS_CONFIRMATION

    def test_user_override(self, pm):
        """User override takes precedence."""
        pm.set_rule("test_tool", PermissionLevel.DENY)
        pm.set_user_override(123, "test_tool", PermissionLevel.ALLOW)
        
        # User 123 should be allowed
        assert pm.check("test_tool", user_id=123) == PermissionDecision.GRANTED
        # User 456 should be denied
        assert pm.check("test_tool", user_id=456) == PermissionDecision.DENIED

    def test_session_permission(self, pm):
        """Session permission takes precedence over user override."""
        pm.set_rule("test_tool", PermissionLevel.DENY)
        pm.set_user_override(123, "test_tool", PermissionLevel.DENY)
        pm.set_session_permission("session_abc", "test_tool", PermissionLevel.ALLOW)
        
        assert pm.check("test_tool", user_id=123, session_id="session_abc") == PermissionDecision.GRANTED

    def test_once_allowance(self, pm):
        """One-time allowance works once then expires."""
        pm.set_rule("test_tool", PermissionLevel.DENY)
        pm.allow_once(123, "test_tool")
        
        # First check should be granted
        assert pm.check("test_tool", user_id=123) == PermissionDecision.GRANTED
        # Second check should be denied (one-time used up)
        assert pm.check("test_tool", user_id=123) == PermissionDecision.DENIED

    def test_audit_log(self, pm):
        """Audit log records checks."""
        pm.check("get_system_info", user_id=123)
        pm.check("run_shell_command", user_id=123)
        
        log = pm.get_audit_log()
        assert len(log) == 2
        assert log[0]["tool_name"] == "get_system_info"
        assert log[0]["decision"] == "granted"
        assert log[1]["tool_name"] == "run_shell_command"
        assert log[1]["decision"] == "needs_confirmation"

    def test_stats_tracking(self, pm):
        """Stats are tracked correctly."""
        pm.check("get_system_info", user_id=1)  # ALLOW
        pm.check("run_shell_command", user_id=1)  # CONFIRM
        pm.set_rule("deny_tool", PermissionLevel.DENY)
        pm.check("deny_tool", user_id=1)  # DENY
        
        stats = pm.get_stats()
        assert stats["total_checks"] == 3
        assert stats["total_granted"] == 1
        assert stats["total_confirmations"] == 1
        assert stats["total_denied"] == 1

    def test_get_rules(self, pm):
        """Can get all rules as dict."""
        rules = pm.get_rules()
        assert isinstance(rules, dict)
        assert all(isinstance(v, str) for v in rules.values())

    @pytest.mark.asyncio
    async def test_publishes_rule_change_event(self, event_bus, pm):
        """Rule changes publish events."""
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("permission.rule_changed", handler)
        pm.set_rule("new_tool", PermissionLevel.ALLOW)
        
        await asyncio.sleep(0.1)
        assert len(events) == 1

    def test_priority_order(self, pm):
        """Priority: once > session > user > global."""
        pm.set_rule("test", PermissionLevel.DENY)  # Global: DENY
        pm.set_user_override(1, "test", PermissionLevel.DENY)  # User: DENY
        pm.set_session_permission("s1", "test", PermissionLevel.DENY)  # Session: DENY
        pm.allow_once(1, "test")  # Once: ALLOW
        
        # Once should win
        assert pm.check("test", user_id=1, session_id="s1") == PermissionDecision.GRANTED


# ── AuditEntry Tests ─────────────────────────────────────────

class TestAuditEntry:
    def test_creation(self):
        entry = AuditEntry(
            tool_name="test",
            user_id=123,
            decision=PermissionDecision.GRANTED,
            timestamp=time.time(),
        )
        assert entry.tool_name == "test"

    def test_to_dict(self):
        entry = AuditEntry(
            tool_name="test",
            user_id=123,
            decision=PermissionDecision.GRANTED,
            timestamp=time.time(),
            details="test details",
        )
        d = entry.to_dict()
        assert d["tool_name"] == "test"
        assert d["decision"] == "granted"
        assert d["details"] == "test details"
