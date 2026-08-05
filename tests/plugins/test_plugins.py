"""
Tests for ORION Plugin SDK (M4.3)
==================================
"""

import asyncio
import json
import os
import pytest
import time

from orion.core.communication.event_bus import EventBus
from orion.plugins.plugin_loader import (
    Plugin, PluginLoader, PluginManifest, PluginStatus, PluginPermission,
)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def plugin_dir(tmp_path):
    return str(tmp_path / "plugins")


@pytest.fixture
def loader(event_bus, plugin_dir):
    return PluginLoader(event_bus, plugin_dir=plugin_dir)


@pytest.fixture
def sample_manifest():
    return PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="A test plugin",
        author="ORION",
        permissions=["read", "write"],
    )


# ── PluginManifest Tests ─────────────────────────────────────

class TestPluginManifest:
    def test_creation(self, sample_manifest):
        assert sample_manifest.name == "test_plugin"
        assert sample_manifest.version == "1.0.0"

    def test_from_dict(self):
        data = {
            "name": "my_plugin",
            "version": "2.0.0",
            "permissions": ["read"],
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.name == "my_plugin"
        assert manifest.version == "2.0.0"

    def test_to_dict(self, sample_manifest):
        d = sample_manifest.to_dict()
        assert d["name"] == "test_plugin"
        assert "read" in d["permissions"]

    def test_from_file(self, tmp_path):
        manifest_file = tmp_path / "plugin.json"
        manifest_file.write_text(json.dumps({
            "name": "file_plugin",
            "version": "1.0.0",
        }))
        
        manifest = PluginManifest.from_file(str(manifest_file))
        assert manifest.name == "file_plugin"


# ── Plugin Tests ──────────────────────────────────────────────

class TestPlugin:
    def test_creation(self, sample_manifest):
        plugin = Plugin(sample_manifest, "/tmp/test")
        assert plugin.manifest.name == "test_plugin"
        assert plugin.status == PluginStatus.LOADED

    def test_register_action(self, sample_manifest):
        plugin = Plugin(sample_manifest, "/tmp/test")
        
        def my_action():
            return "done"
        
        plugin.register_action("do_something", my_action)
        assert "do_something" in plugin.list_actions()

    def test_get_action(self, sample_manifest):
        plugin = Plugin(sample_manifest, "/tmp/test")
        
        def my_action():
            return "done"
        
        plugin.register_action("do_something", my_action)
        assert plugin.get_action("do_something") is not None
        assert plugin.get_action("nonexistent") is None

    @pytest.mark.asyncio
    async def test_execute(self, sample_manifest):
        plugin = Plugin(sample_manifest, "/tmp/test")
        
        async def my_action(**kwargs):
            return {"result": "done", "params": kwargs}
        
        plugin.register_action("do_something", my_action)
        result = await plugin.execute("do_something", {"key": "value"})
        
        assert result["result"] == "done"
        assert result["params"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, sample_manifest):
        plugin = Plugin(sample_manifest, "/tmp/test")
        
        with pytest.raises(ValueError, match="Unknown action"):
            await plugin.execute("nonexistent")

    def test_to_dict(self, sample_manifest):
        plugin = Plugin(sample_manifest, "/tmp/test")
        d = plugin.to_dict()
        
        assert d["name"] == "test_plugin"
        assert d["status"] == "loaded"


# ── PluginLoader Tests ────────────────────────────────────────

class TestPluginLoader:
    def test_initial_state(self, loader):
        assert len(loader.list_plugins()) == 0

    @pytest.mark.asyncio
    async def test_discover_empty(self, loader):
        discovered = await loader.discover_plugins()
        assert discovered == []

    @pytest.mark.asyncio
    async def test_load_plugin(self, loader, plugin_dir):
        # Create a plugin directory with manifest
        plugin_path = os.path.join(plugin_dir, "my_plugin")
        os.makedirs(plugin_path)
        
        manifest = {
            "name": "my_plugin",
            "version": "1.0.0",
            "description": "Test",
        }
        with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
            json.dump(manifest, f)
        
        plugin = await loader.load_plugin(plugin_path)
        
        assert plugin is not None
        assert plugin.manifest.name == "my_plugin"
        assert plugin.status == PluginStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, loader):
        plugin = await loader.load_plugin("/nonexistent/path")
        assert plugin is None

    @pytest.mark.asyncio
    async def test_load_no_manifest(self, loader, plugin_dir):
        plugin_path = os.path.join(plugin_dir, "no_manifest")
        os.makedirs(plugin_path)
        
        plugin = await loader.load_plugin(plugin_path)
        assert plugin is None

    @pytest.mark.asyncio
    async def test_load_all(self, loader, plugin_dir):
        # Create multiple plugins
        for i in range(3):
            path = os.path.join(plugin_dir, f"plugin_{i}")
            os.makedirs(path)
            with open(os.path.join(path, "plugin.json"), "w") as f:
                json.dump({"name": f"plugin_{i}", "version": "1.0.0"}, f)
        
        loaded = await loader.load_all()
        assert loaded == 3
        assert len(loader.list_plugins()) == 3

    @pytest.mark.asyncio
    async def test_get_plugin(self, loader, plugin_dir):
        plugin_path = os.path.join(plugin_dir, "test")
        os.makedirs(plugin_path)
        with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
            json.dump({"name": "test", "version": "1.0.0"}, f)
        
        await loader.load_plugin(plugin_path)
        
        assert loader.get_plugin("test") is not None
        assert loader.get_plugin("nonexistent") is None

    @pytest.mark.asyncio
    async def test_unload_plugin(self, loader, plugin_dir):
        plugin_path = os.path.join(plugin_dir, "test")
        os.makedirs(plugin_path)
        with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
            json.dump({"name": "test", "version": "1.0.0"}, f)
        
        await loader.load_plugin(plugin_path)
        assert loader.unload_plugin("test") is True
        assert loader.get_plugin("test") is None

    @pytest.mark.asyncio
    async def test_unload_nonexistent(self, loader):
        assert loader.unload_plugin("nonexistent") is False

    @pytest.mark.asyncio
    async def test_publishes_events(self, event_bus, loader, plugin_dir):
        events = []
        async def handler(event):
            events.append(event)
        
        await event_bus.subscribe("plugin.loaded", handler)
        
        plugin_path = os.path.join(plugin_dir, "test")
        os.makedirs(plugin_path)
        with open(os.path.join(plugin_path, "plugin.json"), "w") as f:
            json.dump({"name": "test", "version": "1.0.0"}, f)
        
        await loader.load_plugin(plugin_path)
        
        assert len(events) == 1
        assert events[0].payload["name"] == "test"

    def test_stats(self, loader, sample_manifest):
        plugin = Plugin(sample_manifest, "/tmp/test")
        loader._plugins["test"] = plugin
        loader._total_loaded = 1
        
        stats = loader.get_stats()
        assert stats["total_loaded"] == 1
        assert stats["active_plugins"] == 1


# ── PluginPermission Tests ────────────────────────────────────

class TestPluginPermission:
    def test_all_permissions(self):
        assert PluginPermission.READ == "read"
        assert PluginPermission.WRITE == "write"
        assert PluginPermission.EXECUTE == "execute"
        assert PluginPermission.NETWORK == "network"
        assert PluginPermission.SYSTEM == "system"


# ── PluginStatus Tests ────────────────────────────────────────

class TestPluginStatus:
    def test_all_statuses(self):
        assert PluginStatus.DISCOVERED == "discovered"
        assert PluginStatus.LOADED == "loaded"
        assert PluginStatus.ACTIVE == "active"
        assert PluginStatus.ERROR == "error"
        assert PluginStatus.DISABLED == "disabled"
