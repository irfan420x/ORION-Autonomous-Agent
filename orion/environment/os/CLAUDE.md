"""# CLAUDE.md - OS Control Subsystem

## 1. Overview
ORION's OS Control Subsystem provides a robust and secure interface for interacting with the underlying operating system. It enables ORION to perform fundamental OS operations such as managing files, processes, and windows, abstracting away platform-specific complexities.

## 2. Components
- **FileManager (`file_manager.py`):** Handles file and directory operations (read, write, delete, copy, move, list).
- **ProcessManager (`process_manager.py`):** Manages running processes (start, stop, query status).
- **WindowManager (`window_manager.py`):** Controls GUI windows (open, close, resize, move, focus).
- **TerminalManager (`terminal_manager.py`):** Provides an interface for executing shell commands and capturing their output.

## 3. Interfaces (Contracts)
OS control-related data structures are defined in `orion/contracts/os_contracts.py`.

### 3.1 FileManager Interface
- `async read_file(path: str) -> str`: Reads the content of a file.
- `async write_file(path: str, content: str)`: Writes content to a file.
- `async delete_file(path: str)`: Deletes a file or directory.

### 3.2 ProcessManager Interface
- `async start_process(command: List[str], cwd: Optional[str] = None) -> ProcessInfo`: Starts a new process.
- `async terminate_process(pid: int)`: Terminates a running process.

### 3.3 WindowManager Interface
- `async get_active_window() -> WindowInfo`: Retrieves information about the currently active window.
- `async focus_window(window_id: str)`: Brings a specific window to the foreground.

### 3.4 TerminalManager Interface
- `async execute_command(command: str, timeout: Optional[int] = None) -> CommandResult`: Executes a shell command.

## 4. Dependencies
- **Internal:** `orion.contracts.os_contracts`, `orion.core.communication.event_bus`, `orion.security.permission_manager`, `orion.world_model.file_graph`, `orion.world_model.process_graph`, `orion.world_model.window_graph`
- **External:** `asyncio`, `subprocess`, `psutil`, `pygetwindow` (or platform-specific alternatives).

## 5. Build Order & Verification (Phase 5 - M5.1)
1. Define OS control-related Pydantic models in `orion/contracts/os_contracts.py`.
2. Implement `FileManager` with basic read/write/delete operations.
3. Implement `ProcessManager` with start/terminate/query operations.
4. Implement `WindowManager` with basic active window retrieval and focus.
5. Implement `TerminalManager` for executing shell commands.
6. Create a demo script (`examples/os_control_demo.py`) to demonstrate basic OS interactions.
7. Ensure unit tests for all OS Control modules pass.
"""
