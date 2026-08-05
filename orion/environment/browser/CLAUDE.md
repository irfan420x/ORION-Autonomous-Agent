"""# CLAUDE.md - Browser Automation Subsystem

## 1. Overview
ORION's Browser Automation Subsystem provides robust capabilities for interacting with web browsers, enabling the agent to perform web-based tasks, extract information, and automate online workflows. It leverages the Playwright framework for cross-browser compatibility and advanced automation features.

## 2. Components
- **BrowserManager (`browser_manager.py`):** Manages browser instances, contexts, pages, and sessions. It handles launching, closing, and configuring browsers.
- **PageNavigator (`page_navigator.py`):** Provides high-level functions for navigating to URLs, clicking elements, filling forms, and extracting data from web pages.
- **SessionManager (`session_manager.py`):** Manages browser sessions, including cookies, local storage, and user profiles, ensuring consistent and isolated browsing environments.

## 3. Interfaces (Contracts)
Browser automation-related data structures are defined in `orion/contracts/browser_contracts.py`.

### 3.1 BrowserManager Interface
- `async launch_browser(headless: bool = True, profile_path: Optional[str] = None) -> BrowserContextInfo`: Launches a new browser instance or context.
- `async close_browser(context_id: str)`: Closes a specific browser context.
- `async new_page(context_id: str) -> PageInfo`: Opens a new page within a browser context.

### 3.2 PageNavigator Interface
- `async goto(page_id: str, url: str)`: Navigates a page to a specified URL.
- `async click(page_id: str, selector: str)`: Clicks an element on the page.
- `async fill(page_id: str, selector: str, value: str)`: Fills a text input field.
- `async extract_text(page_id: str, selector: str) -> str`: Extracts text content from an element.
- `async take_screenshot(page_id: str, path: str)`: Takes a screenshot of the current page.

## 4. Dependencies
- **Internal:** `orion.contracts.browser_contracts`, `orion.core.communication.event_bus`, `orion.security.permission_manager`, `orion.world_model.window_graph`
- **External:** `playwright`, `asyncio`.

## 5. Build Order & Verification (Phase 5 - M5.3)
1. Define browser-related Pydantic models in `orion/contracts/browser_contracts.py`.
2. Implement `BrowserManager` to launch and manage Playwright browser contexts.
3. Implement `PageNavigator` for basic navigation, clicking, and text extraction.
4. Implement `SessionManager` for handling cookies and local storage.
5. Create a demo script (`examples/browser_automation_demo.py`) to automate a simple web task (e.g., navigating to a website, searching, and extracting results).
6. Ensure unit tests for all Browser Automation modules pass.
"""
