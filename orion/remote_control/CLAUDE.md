"""# CLAUDE.md - Remote Control Subsystem

## 1. Overview
ORION's Remote Control Subsystem enables users to interact with and manage the agent from external interfaces, such as Telegram bots, REST APIs, and WebSockets. This allows for flexible control and monitoring of ORION's operations from various devices and applications.

## 2. Components
- **TelegramController (`telegram_controller.py`):** Handles incoming commands and messages from Telegram, authenticates users, and routes requests to the appropriate ORION modules.
- **APIController (`api_controller.py`):** Exposes a RESTful API for programmatic interaction with ORION, supporting task submission, status queries, and configuration management.
- **WebSocketController (`websocket_controller.py`):** Provides a real-time, bidirectional communication channel for streaming events, logs, and interactive control.
- **AuthManager (`auth_manager.py`):** Manages user authentication and authorization for remote access, integrating with the User-Controlled Permission Model.

## 3. Interfaces (Contracts)
Remote control-related data structures are defined in `orion/contracts/remote_contracts.py`.

### 3.1 TelegramController Interface
- `async process_telegram_update(update: TelegramUpdate) -> TelegramResponse`: Processes an incoming Telegram update.

### 3.2 APIController Interface
- `async handle_api_request(request: APIRequest) -> APIResponse`: Handles incoming REST API requests.

### 3.3 WebSocketController Interface
- `async send_event(event: Event)`: Sends an ORION event over WebSocket.
- `async receive_command() -> RemoteCommand`: Receives a command from a connected WebSocket client.

## 4. Dependencies
- **Internal:** `orion.contracts.remote_contracts`, `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`, `orion.security.permission_manager`
- **External:** `python-telegram-bot`, `FastAPI`, `uvicorn`, `websockets`, `asyncio`.

## 5. Build Order & Verification (Phase 6 - M6.2)
1. Define remote control-related Pydantic models in `orion/contracts/remote_contracts.py`.
2. Implement `AuthManager` for basic user authentication.
3. Implement `TelegramController` to receive and respond to simple commands (e.g., `/status`).
4. Implement `APIController` with a basic endpoint for task submission.
5. Implement `WebSocketController` for streaming ORION events.
6. Create a demo script (`examples/remote_control_demo.py`) to demonstrate sending a command via Telegram (mocked) and receiving a response.
7. Ensure unit tests for all Remote Control modules pass.
"""
