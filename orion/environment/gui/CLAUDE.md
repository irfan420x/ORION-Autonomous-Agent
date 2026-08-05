"""# CLAUDE.md - GUI Automation Subsystem

## 1. Overview
ORION's GUI Automation Subsystem enables the agent to interact with graphical user interfaces of desktop applications. This is crucial for automating tasks that involve clicking buttons, typing into fields, and navigating menus, mimicking human interaction with the OS.

## 2. Components
- **GUIManager (`gui_manager.py`):** Provides high-level functions for interacting with GUI elements, abstracting platform-specific details.
- **AccessibilityAdapter (`accessibility_adapter.py`):** Interfaces with OS-native accessibility APIs (e.g., AT-SPI2 on Linux, UI Automation on Windows) to discover and manipulate UI elements.
- **InputEmulator (`input_emulator.py`):** Emulates mouse movements, clicks, and keyboard inputs.

## 3. Interfaces (Contracts)
GUI automation-related data structures are defined in `orion/contracts/gui_contracts.py`.

### 3.1 GUIManager Interface
- `async click_element(selector: str)`: Clicks a UI element identified by a selector (e.g., text, accessibility ID).
- `async type_text(selector: str, text: str)`: Types text into a UI element.
- `async find_element(selector: str) -> UIElementInfo`: Finds a UI element and returns its information.

## 4. Dependencies
- **Internal:** `orion.contracts.gui_contracts`, `orion.core.communication.event_bus`, `orion.security.permission_manager`, `orion.environment.vision.vision_engine`
- **External:** `pyautogui`, `pygetwindow`, `pyatspi` (Linux), `pywinauto` (Windows), `asyncio`.

## 5. Build Order & Verification (Phase 5 - M5.2)
1. Define GUI-related Pydantic models in `orion/contracts/gui_contracts.py`.
2. Implement `InputEmulator` for basic mouse/keyboard actions.
3. Implement `AccessibilityAdapter` (initially for a single OS, e.g., Linux AT-SPI2) to find UI elements.
4. Implement `GUIManager` to combine input emulation and element discovery.
5. Create a demo script (`examples/gui_automation_demo.py`) to automate a simple desktop application task (e.g., opening calculator and typing).
6. Ensure unit tests for all GUI Automation modules pass.
"""
