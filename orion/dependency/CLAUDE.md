"""# CLAUDE.md - Dependency Management Subsystem

## 1. Overview
ORION's Dependency Management Subsystem is responsible for ensuring that all necessary software, libraries, and binaries are correctly installed, updated, and healthy. It allows ORION to adapt to various operating environments and automatically resolve missing dependencies, crucial for its self-healing capabilities.

## 2. Components
- **DependencyEngine (`dependency_engine.py`):** Detects missing dependencies, manages their installation, and verifies their versions. It interfaces with platform-specific package managers.
- **PlatformMapper (`platform_mapper.py`):** Maps generic tool names (e.g., 'nmap') to platform-specific commands or package names (e.g., 'nmap' on Linux, 'nmap' on macOS via Homebrew).

## 3. Interfaces (Contracts)
Dependency-related data structures are defined in `orion/contracts/dependency_contracts.py`.

### 3.1 DependencyEngine Interface
- `async check_dependency(name: str) -> DependencyStatus`: Checks if a dependency is installed and meets version requirements.
- `async install_dependency(name: str) -> bool`: Attempts to install a missing dependency using the appropriate package manager.
- `async update_dependency(name: str) -> bool`: Attempts to update an installed dependency.
- `async repair_dependency(name: str) -> bool`: Attempts to repair a corrupted or non-functional dependency.

## 4. Dependencies
- **Internal:** `orion.contracts.dependency_contracts`, `orion.core.communication.event_bus`, `orion.core.runtime.adaptive_runtime`
- **External:** `subprocess` (for executing package managers), `platform` (for OS detection), `asyncio`.

## 5. Build Order & Verification (Phase 2 - M2.2)
1. Define dependency-related Pydantic models in `orion/contracts/dependency_contracts.py`.
2. Implement `PlatformMapper` to handle OS-specific tool/package names.
3. Implement `DependencyEngine` with `check_dependency` and `install_dependency` (initially for Python packages via `pip`).
4. Create a demo script (`examples/dependency_engine_demo.py`) to demonstrate checking and installing a Python package.
5. Ensure unit tests for `DependencyEngine` pass.
"""
