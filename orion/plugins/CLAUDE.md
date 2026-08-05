"""# CLAUDE.md - Plugin System

## 1. Overview
ORION's Plugin System provides a robust and secure mechanism for extending its functionality without modifying the core codebase. It allows third-party developers to integrate new tools, skills, or specialized agents, fostering a vibrant ecosystem around ORION.

## 2. Components
- **PluginManager (`plugin_manager.py`):** Discovers, loads, validates, and manages the lifecycle of plugins. It ensures plugins adhere to security policies and resource constraints.
- **PluginSandbox (`plugin_sandbox.py`):** Provides an isolated execution environment for plugins, mitigating security risks and preventing interference with core ORION operations.

## 3. Interfaces (Contracts)
Plugin-related data structures are defined in `orion/contracts/plugin_contracts.py`.

### 3.1 PluginManager Interface
- `async load_plugin(path: str) -> PluginManifest`: Loads a plugin from a specified path, validates its manifest, and prepares it for activation.
- `async activate_plugin(plugin_id: str) -> bool`: Activates a loaded plugin, integrating its functionalities into ORION.
- `async deactivate_plugin(plugin_id: str) -> bool`: Deactivates an active plugin, removing its functionalities.
- `async get_active_plugins() -> List[PluginManifest]`: Returns a list of currently active plugins.

## 4. Dependencies
- **Internal:** `orion.contracts.plugin_contracts`, `orion.core.communication.event_bus`, `orion.security.permission_manager`, `orion.resource.resource_manager`
- **External:** `asyncio`, `pyyaml` (for plugin manifests), `subprocess` (for sandbox isolation).

## 5. Build Order & Verification (Phase 4 - M4.3)
1. Define plugin-related Pydantic models in `orion/contracts/plugin_contracts.py`.
2. Implement `PluginManager` to load and validate plugin manifests.
3. Implement `PluginSandbox` (initially as a basic process isolation, later with more advanced techniques).
4. Create a sample plugin manifest file (`plugins/sample_plugin/plugin.yaml`).
5. Create a demo script (`examples/plugin_system_demo.py`) to demonstrate loading and activating a mock plugin.
6. Ensure unit tests for `PluginManager` and `PluginSandbox` pass.
"""
