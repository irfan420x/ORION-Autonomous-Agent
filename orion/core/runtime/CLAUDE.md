# CLAUDE.md - Core Runtime Subsystem

## 1. Overview
This subsystem provides the foundational runtime environment for ORION, managing its lifecycle, resource allocation, and adaptive behavior based on system capabilities. It ensures ORION operates efficiently across diverse hardware and environmental conditions.

## 2. Components
- **AdaptiveRuntime (`runtime.py`):** Detects hardware capabilities, negotiates operating modes (e.g., `full`, `cpu_only`, `low_memory`), and dynamically loads/unloads modules.
- **HardwareDetector (`hardware_detector.py` in `orion-rs`):** A Rust-based component responsible for scanning and reporting system hardware specifications (CPU, GPU, RAM, etc.).

## 3. Interfaces (Contracts)
- **HardwareProfile (`orion.contracts.runtime_contracts.py`):** Pydantic model defining the structure of hardware detection reports.
- **OperatingMode (`orion.contracts.runtime_contracts.py`):** Enum defining various operational modes.

### 3.1 AdaptiveRuntime Interface
- `async initialize()`: Performs initial hardware scan and sets the operating mode.
- `async get_current_operating_mode() -> OperatingMode`: Retrieves the currently active operating mode.
- `async get_hardware_profile() -> HardwareProfile`: Retrieves the detected hardware profile.
- `async switch_operating_mode(mode: OperatingMode)`: Forces a switch to a specific operating mode (if allowed by policy).

## 4. Dependencies
- **Internal:** `orion.contracts.runtime_contracts`, `orion.core.communication.event_bus`, `orion.resource.resource_manager`
- **External:** `psutil` (Python for system info), `orion-rs/hardware_detector` (Rust for low-level hardware detection)

## 5. Build Order & Verification (Phase 1 - M1.1/M1.2, Phase 2 - M2.1)
1. Define `HardwareProfile` and `OperatingMode` in `orion/contracts/runtime_contracts.py`.
2. Implement `HardwareDetector` in Rust (`orion-rs/src/hardware_detector.rs`) to report basic CPU/RAM info.
3. Implement `AdaptiveRuntime` in Python to read `config/system.yaml`, use `HardwareDetector` output, and set initial `OperatingMode`.
4. Create a demo script (`examples/adaptive_runtime_demo.py`) to show hardware detection and mode switching.
5. Ensure unit tests for `AdaptiveRuntime` pass.
