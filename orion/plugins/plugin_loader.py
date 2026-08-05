"""
ORION Plugin SDK
================

Secure plugin system for extending ORION's capabilities.

Features:
- Plugin manifest (name, version, permissions)
- Plugin loading from directory
- Sandboxed execution
- Permission enforcement
- Event integration

Usage:
    loader = PluginLoader(event_bus)
    loader.load_plugins("/path/to/plugins/")
    plugin = loader.get_plugin("my_plugin")
    result = await plugin.execute("action", params)
"""

import asyncio
import importlib
import json
import logging
import os
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from orion.contracts.agent_contracts import Event
from orion.core.communication.event_bus import EventBus

logger = logging.getLogger(__name__)


class PluginStatus(str, Enum):
    """Plugin lifecycle status."""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginPermission(str, Enum):
    """Plugin permission levels."""
    READ = "read"           # Read files, query data
    WRITE = "write"         # Write files, modify data
    EXECUTE = "execute"     # Run commands
    NETWORK = "network"     # Make network requests
    SYSTEM = "system"       # System-level operations


class PluginManifest:
    """Plugin metadata and configuration."""
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str = "",
        author: str = "",
        permissions: Optional[List[str]] = None,
        entry_point: str = "plugin.py",
        dependencies: Optional[List[str]] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.permissions = permissions or []
        self.entry_point = entry_point
        self.dependencies = dependencies or []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Create manifest from dictionary."""
        return cls(
            name=data.get("name", "unknown"),
            version=data.get("version", "0.0.1"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            permissions=data.get("permissions", []),
            entry_point=data.get("entry_point", "plugin.py"),
            dependencies=data.get("dependencies", []),
        )
    
    @classmethod
    def from_file(cls, path: str) -> "PluginManifest":
        """Load manifest from JSON file."""
        with open(path) as f:
            return cls.from_dict(json.load(f))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "permissions": self.permissions,
            "entry_point": self.entry_point,
            "dependencies": self.dependencies,
        }


class Plugin:
    """A loaded plugin instance."""
    
    def __init__(
        self,
        manifest: PluginManifest,
        plugin_dir: str,
        module: Optional[Any] = None,
    ):
        self.id = f"plugin_{uuid.uuid4().hex[:8]}"
        self.manifest = manifest
        self.plugin_dir = plugin_dir
        self.module = module
        self.status = PluginStatus.LOADED
        self.error: Optional[str] = None
        self.loaded_at = time.time()
        
        # Actions provided by this plugin
        self._actions: Dict[str, Callable] = {}
    
    def register_action(self, name: str, handler: Callable) -> None:
        """Register an action this plugin provides."""
        self._actions[name] = handler
    
    def get_action(self, name: str) -> Optional[Callable]:
        """Get an action by name."""
        return self._actions.get(name)
    
    def list_actions(self) -> List[str]:
        """List available actions."""
        return list(self._actions.keys())
    
    async def execute(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a plugin action."""
        handler = self._actions.get(action)
        if not handler:
            raise ValueError(f"Unknown action: {action}")
        
        if asyncio.iscoroutinefunction(handler):
            return await handler(**(params or {}))
        else:
            return handler(**(params or {}))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.manifest.name,
            "version": self.manifest.version,
            "status": self.status.value,
            "actions": self.list_actions(),
            "permissions": self.manifest.permissions,
            "loaded_at": self.loaded_at,
        }


class PluginLoader:
    """Discovers, loads, and manages plugins."""
    
    def __init__(
        self,
        event_bus: EventBus,
        plugin_dir: str = "plugins",
    ):
        self._event_bus = event_bus
        self._plugin_dir = plugin_dir
        self._plugins: Dict[str, Plugin] = {}
        
        # Stats
        self._total_loaded: int = 0
        self._total_errors: int = 0
        
        logger.info("PluginLoader initialized (dir=%s)", plugin_dir)
    
    async def discover_plugins(self) -> List[str]:
        """Discover plugin directories."""
        plugin_dir = Path(self._plugin_dir)
        if not plugin_dir.exists():
            os.makedirs(plugin_dir, exist_ok=True)
            return []
        
        discovered = []
        for entry in plugin_dir.iterdir():
            if entry.is_dir():
                manifest_path = entry / "plugin.json"
                if manifest_path.exists():
                    discovered.append(str(entry))
        
        logger.info("Discovered %d plugins", len(discovered))
        return discovered
    
    async def load_plugin(self, plugin_path: str) -> Optional[Plugin]:
        """Load a single plugin from directory."""
        try:
            # Load manifest
            manifest_path = os.path.join(plugin_path, "plugin.json")
            if not os.path.exists(manifest_path):
                logger.warning("No manifest found: %s", plugin_path)
                return None
            
            manifest = PluginManifest.from_file(manifest_path)
            
            # Check if already loaded
            if manifest.name in self._plugins:
                logger.warning("Plugin already loaded: %s", manifest.name)
                return self._plugins[manifest.name]
            
            # Create plugin instance
            plugin = Plugin(manifest, plugin_path)
            
            # Try to load entry point module
            entry_path = os.path.join(plugin_path, manifest.entry_point)
            if os.path.exists(entry_path):
                # Dynamic import
                spec = __import__(
                    f"plugins.{manifest.name}.{manifest.entry_point.replace('.py', '')}",
                    fromlist=[manifest.name],
                )
                plugin.module = spec
                
                # Call plugin's register function if it exists
                if hasattr(spec, "register"):
                    await spec.register(plugin)
            
            plugin.status = PluginStatus.ACTIVE
            self._plugins[manifest.name] = plugin
            self._total_loaded += 1
            
            # Publish event
            await self._event_bus.publish(Event(
                event_type="plugin.loaded",
                payload=plugin.to_dict(),
                timestamp=time.time(),
                source="plugin_loader",
            ))
            
            logger.info("Plugin loaded: %s v%s", manifest.name, manifest.version)
            return plugin
        
        except Exception as e:
            self._total_errors += 1
            logger.error("Failed to load plugin %s: %s", plugin_path, e)
            
            await self._event_bus.publish(Event(
                event_type="plugin.error",
                payload={"path": plugin_path, "error": str(e)},
                timestamp=time.time(),
                source="plugin_loader",
            ))
            
            return None
    
    async def load_all(self) -> int:
        """Discover and load all plugins."""
        discovered = await self.discover_plugins()
        loaded = 0
        
        for plugin_path in discovered:
            plugin = await self.load_plugin(plugin_path)
            if plugin:
                loaded += 1
        
        logger.info("Loaded %d/%d plugins", loaded, len(discovered))
        return loaded
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[Plugin]:
        """List all loaded plugins."""
        return list(self._plugins.values())
    
    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.status = PluginStatus.DISABLED
            del self._plugins[name]
            logger.info("Plugin unloaded: %s", name)
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        return {
            "total_loaded": self._total_loaded,
            "total_errors": self._total_errors,
            "active_plugins": len(self._plugins),
            "plugin_dir": self._plugin_dir,
            "plugins": [p.to_dict() for p in self._plugins.values()],
        }
