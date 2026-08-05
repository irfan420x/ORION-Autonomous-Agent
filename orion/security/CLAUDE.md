"""# CLAUDE.md - Security Subsystem

## 1. Overview
ORION's Security Subsystem is paramount for protecting the system, user data, and privacy. It implements a robust User-Controlled Permission Model, secures sensitive information, and provides auditing capabilities to ensure transparency and accountability.

## 2. Components
- **PermissionManager (`permission_manager.py`):** Enforces the User-Controlled Permission Model, checking if an agent or tool has the necessary permissions for an action.
- **SecretsVault (`secrets_vault.py`):** Securely stores and manages sensitive information like API keys and credentials, using encryption and ephemeral access.
- **AuditLogger (`audit_logger.py`):** Records all sensitive actions and system events for auditing and compliance purposes.
- **SandboxManager (`sandbox_manager.py`):** Manages isolated environments for executing untrusted code or plugins, limiting their access to core system resources.

## 3. Interfaces (Contracts)
Security-related data structures are defined in `orion/contracts/security_contracts.py`.

### 3.1 PermissionManager Interface
- `async check_permission(action: str, agent_id: str) -> PermissionStatus`: Checks if an agent has permission for a specific action.
- `async request_permission(action: str, agent_id: str) -> bool`: Requests user approval for a high-risk action.

### 3.2 SecretsVault Interface
- `async get_secret(key: str) -> Optional[str]`: Retrieves a secret securely.
- `async store_secret(key: str, value: str)`: Stores an encrypted secret.

### 3.3 AuditLogger Interface
- `async log_action(action: AuditAction)`: Records an auditable action.

## 4. Dependencies
- **Internal:** `orion.contracts.security_contracts`, `orion.core.communication.event_bus`, `orion.ux.notification_service`
- **External:** `cryptography` (for encryption), `asyncio`.

## 5. Build Order & Verification (Phase 6 - M6.4)
1. Define security-related Pydantic models in `orion/contracts/security_contracts.py`.
2. Implement `SecretsVault` with basic encryption/decryption for storing secrets.
3. Implement `AuditLogger` to record actions to a file or database.
4. Implement `PermissionManager` to enforce rules from `config/permission_config.yaml`.
5. Implement `SandboxManager` (initially as a basic process wrapper).
6. Create a demo script (`examples/security_demo.py`) to demonstrate permission checks, secret storage, and audit logging.
7. Ensure unit tests for all Security modules pass.
"""
