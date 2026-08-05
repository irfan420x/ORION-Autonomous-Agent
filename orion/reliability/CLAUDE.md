# CLAUDE.md - Reliability Subsystem

## 1. Overview
ORION's Reliability Subsystem is designed to ensure the agent's continuous operation, fault tolerance, and graceful recovery from errors. It encompasses mechanisms for self-healing, robust error handling, and a comprehensive recovery matrix to maintain system stability and data integrity.

## 2. Components
- **SelfHealingEngine (`self_healing_engine.py`):** Monitors system health, detects anomalies, and initiates automated repair processes for corrupted data, missing dependencies, or crashed services.
- **RecoveryMatrix (`recovery_matrix.py`):** Implements a predefined protocol for handling various types of errors and failures, determining appropriate recovery actions (retry, replan, escalate).
- **DataIntegrityManager (`data_integrity_manager.py`):** Regularly checks the integrity of critical data stores (e.g., `project_state.json`, SQLite databases) and initiates recovery if corruption is detected.

## 3. Interfaces (Contracts)
Reliability-related data structures are defined in `orion/contracts/reliability_contracts.py`.

### 3.1 SelfHealingEngine Interface
- `async monitor_system_health()`: Continuously monitors ORION's components and system resources.
- `async initiate_repair(issue: str) -> bool`: Attempts to repair a detected issue.

### 3.2 RecoveryMatrix Interface
- `async handle_failure(failure_report: FailureReport) -> RecoveryAction`: Determines the appropriate recovery action for a given failure.
- `async get_backoff_strategy(error_type: str) -> BackoffStrategy`: Provides a backoff strategy for transient errors.

### 3.3 DataIntegrityManager Interface
- `async check_integrity(data_store_path: str) -> bool`: Checks the integrity of a specified data store.
- `async restore_from_backup(data_store_path: str) -> bool`: Restores a data store from its last known good backup.

## 4. Dependencies
- **Internal:** `orion.contracts.reliability_contracts`, `orion.contracts.learning_contracts`, `orion.core.communication.event_bus`, `orion.core.state.state_machine`, `orion.dependency.dependency_engine`, `orion.security.audit_logger`
- **External:** `asyncio`, `pyyaml` (for `failure_matrix.yaml`).

## 5. Build Order & Verification (Phase 7 - M7.4)
1. Define reliability-related Pydantic models in `orion/contracts/reliability_contracts.py`.
2. Implement `DataIntegrityManager` for basic checksum verification of `project_state.json`.
3. Implement `RecoveryMatrix` to read `config/failure_matrix.yaml` and determine simple recovery actions.
4. Implement `SelfHealingEngine` to monitor for basic issues and trigger recovery.
5. Create a demo script (`examples/reliability_demo.py`) to simulate a failure and demonstrate recovery.
6. Ensure unit tests for all Reliability modules pass.
