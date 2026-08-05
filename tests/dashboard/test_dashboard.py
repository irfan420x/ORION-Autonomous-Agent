"""
Tests for ORION Dashboard (M5.1)
=================================
"""

import pytest
from orion.dashboard.api import DashboardAPI


@pytest.fixture
def api():
    return DashboardAPI()


class TestDashboardAPI:
    def test_system_overview(self, api):
        result = api.get_system_overview()
        assert "cpu" in result
        assert "memory" in result
        assert "disk" in result
        assert "status" in result

    def test_processes(self, api):
        result = api.get_processes(limit=5)
        assert isinstance(result, list)

    def test_memory_stats(self, api):
        result = api.get_memory_stats()
        assert isinstance(result, dict)

    def test_tasks(self, api):
        result = api.get_tasks()
        assert isinstance(result, list)

    def test_runtime_status(self, api):
        result = api.get_runtime_status()
        assert isinstance(result, dict)

    def test_navigation_items(self, api):
        result = api.get_navigation_items()
        assert len(result) == 8
        assert result[0]["id"] == "dashboard"

    def test_quick_actions(self, api):
        result = api.get_quick_actions()
        assert len(result) == 8

    def test_schedule(self, api):
        result = api.get_schedule()
        assert len(result) == 5

    def test_dock_apps(self, api):
        result = api.get_dock_apps()
        assert len(result) == 9

    def test_execute_action(self, api):
        result = api.execute_action("unknown_action")
        assert result["success"] is False
