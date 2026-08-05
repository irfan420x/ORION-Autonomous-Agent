"""# CLAUDE.md - Tool System

## 1. Overview
ORION's Tool System provides a standardized way for agents to interact with external programs, utilities, and APIs. It abstracts the complexities of tool invocation, argument parsing, and output handling, allowing agents to focus on higher-level reasoning. The system supports both built-in OS tools (like `nmap`, `git`) and custom Python-based tools.

## 2. Components
- **ToolRegistry (`tool_registry.py`):** Maintains a catalog of all available tools, their schemas, capabilities, and execution methods. It loads tool definitions from `config/tool_config.yaml`.
- **ToolExecutor (`tool_executor.py`):** Responsible for executing a specific tool, handling its input, running the command/function, and parsing its output into a structured format.
- **ToolWrapper (`tool_wrapper.py`):** Provides a common interface for wrapping different types of tools (CLI, Python function, API) into a standardized format that the `ToolExecutor` can understand.

## 3. Interfaces (Contracts)
Tool-related data structures are defined in `orion/contracts/tool_contracts.py`.

### 3.1 ToolRegistry Interface
- `async load_tools(config_path: str)`: Loads tool definitions from the specified configuration file.
- `async get_tool_info(tool_id: str) -> ToolDefinition`: Retrieves the definition of a specific tool.
- `async find_tools_by_capability(capability: str) -> List[ToolDefinition]`: Finds tools that possess a given capability.

### 3.2 ToolExecutor Interface
- `async execute_tool(tool_id: str, args: Dict[str, Any]) -> ToolExecutionResult`: Executes a tool with the given arguments and returns a structured result.

## 4. Dependencies
- **Internal:** `orion.contracts.tool_contracts`, `orion.core.communication.event_bus`, `orion.security.permission_manager`, `orion.dependency.dependency_engine`
- **External:** `asyncio`, `subprocess` (for CLI tools), `pyyaml` (for config parsing), `jsonschema` (for schema validation).

## 5. Build Order & Verification (Phase 4 - M4.4)
1. Define tool-related Pydantic models in `orion/contracts/tool_contracts.py`.
2. Implement `ToolRegistry` to load tool definitions from `config/tool_config.yaml`.
3. Implement `ToolExecutor` to execute simple CLI tools (e.g., `ls`, `echo`).
4. Implement `ToolWrapper` for basic CLI commands.
5. Create a sample tool definition in `config/tool_config.yaml`.
6. Create a demo script (`examples/tool_system_demo.py`) to demonstrate tool discovery and execution.
7. Ensure unit tests for `ToolRegistry` and `ToolExecutor` pass.
"""
