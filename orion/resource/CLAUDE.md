# CLAUDE.md - Resource Management Subsystem

## 1. Overview
ORION's Resource Management Subsystem is responsible for monitoring, allocating, and managing system resources (CPU, RAM, Disk I/O, Network) to ensure efficient operation and prevent resource exhaustion. It works closely with the Adaptive Runtime to adjust ORION's behavior based on available resources.

## 2. Components
- **ResourceManager (`resource_manager.py`):** Provides an API to query current resource usage and apply resource limits.
- **ResourceMonitor (`resource_monitor.py` in `orion-rs`):** A Rust-based component for low-level, high-performance monitoring of system resources.

## 3. Interfaces (Contracts)
Resource-related data structures are defined in `orion/contracts/resource_contracts.py`.

### 3.1 ResourceManager Interface
- `async get_cpu_usage() -> float`: Returns current CPU usage percentage.
- `async get_memory_usage() -> float`: Returns current RAM usage percentage.
- `async get_disk_usage(path: str) -> Dict[str, float]`: Returns disk usage for a given path.
- `async set_resource_limit(resource_type: str, limit: Any)`: Sets a limit for a specific resource (e.g., max RAM for a process).

## 4. Dependencies
- **Internal:** `orion.contracts.resource_contracts`, `orion.core.communication.event_bus`, `orion.core.runtime.adaptive_runtime`
- **External:** `psutil` (Python), `orion-rs/resource_monitor` (Rust)

## 5. Build Order & Verification (Phase 2 - M2.1)
1. Define resource-related Pydantic models in `orion/contracts/resource_contracts.py`.
2. Implement `ResourceMonitor` in Rust (`orion-rs/src/resource_monitor.rs`) to provide basic CPU/RAM usage.
3. Implement `ResourceManager` in Python to interface with `ResourceMonitor` and `psutil`.
4. Create a demo script (`examples/resource_manager_demo.py`) to show resource monitoring.
5. Ensure unit tests for `ResourceManager` pass.
