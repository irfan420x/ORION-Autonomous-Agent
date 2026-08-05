"""# CLAUDE.md - User Experience (UX) Subsystem

## 1. Overview
ORION's User Experience (UX) Subsystem is dedicated to providing an intuitive, responsive, and Jarvis-like interface for the user. It encompasses the desktop GUI, notifications, and visual feedback mechanisms, ensuring a seamless interaction between the user and the autonomous agent.

## 2. Components
- **DesktopGUI (`desktop_gui.py`):** The main application window, built with Tauri (Rust + React/TypeScript), providing a dashboard, chat interface, and task visualization.
- **OverlayManager (`overlay_manager.py`):** Manages a transparent, non-interactive overlay window for displaying status, notifications, and visual cues (e.g., Floating Orb, voice animations).
- **NotificationService (`notification_service.py`):** Handles system-wide notifications, alerts, and user prompts for confirmation.
- **FloatingOrb (`floating_orb.py`):** A visual indicator of ORION's presence and current state, typically a small, animated icon on the desktop.

## 3. Interfaces (Contracts)
UX-related data structures are defined in `orion/contracts/ux_contracts.py`.

### 3.1 DesktopGUI Interface
- `async show_dashboard()`: Displays the main ORION dashboard.
- `async show_chat_interface()`: Activates the chat interface for text-based interaction.
- `async update_task_panel(tasks: List[Task])`: Updates the task visualization panel.

### 3.2 OverlayManager Interface
- `async show_overlay(content: str, duration: Optional[float] = None)`: Displays content on the desktop overlay.
- `async hide_overlay()`: Hides the desktop overlay.
- `async animate_orb(state: str)`: Changes the animation of the Floating Orb based on ORION's state.

### 3.3 NotificationService Interface
- `async send_notification(title: str, message: str, type: NotificationType)`: Sends a system notification.
- `async request_confirmation(prompt: str) -> bool`: Prompts the user for a yes/no confirmation.

## 4. Dependencies
- **Internal:** `orion.contracts.ux_contracts`, `orion.contracts.agent_contracts`, `orion.core.communication.event_bus`, `orion.remote_control.websocket_controller`
- **External:** `Tauri` (Rust, React, TypeScript), `asyncio`.

## 5. Build Order & Verification (Phase 6 - M6.3)
1. Define UX-related Pydantic models in `orion/contracts/ux_contracts.py`.
2. Implement `NotificationService` for basic system notifications.
3. Implement `FloatingOrb` (initially as a simple visual indicator).
4. Implement `OverlayManager` to display basic text on a transparent overlay.
5. Implement `DesktopGUI` (Tauri frontend) with a basic window and integration points for other components.
6. Create a demo script (`examples/ux_demo.py`) to demonstrate notifications and overlay display.
7. Ensure unit tests for all UX modules pass.
"""
