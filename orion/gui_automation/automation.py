"""
ORION GUI Automation
====================

Control desktop applications using mouse, keyboard, and accessibility APIs.

Features:
- Mouse control (move, click, drag)
- Keyboard control (type, hotkeys)
- Window management (find, focus, resize)
- Screenshot capture
- UI element detection

Usage:
    auto = GUIAutomation()
    auto.move_mouse(100, 200)
    auto.click()
    auto.type_text("Hello")
    auto.screenshot("/tmp/screen.png")
"""

import logging
import os
import subprocess
import time
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class GUIAutomation:
    """Desktop GUI automation using xdotool and related tools."""
    
    def __init__(self):
        self._check_dependencies()
        logger.info("GUIAutomation initialized")
    
    def _check_dependencies(self):
        """Check if required tools are available."""
        tools = ['xdotool', 'xwininfo', 'xclip']
        missing = []
        for tool in tools:
            try:
                subprocess.run(['which', tool], capture_output=True, check=True)
            except subprocess.CalledProcessError:
                missing.append(tool)
        
        if missing:
            logger.warning("Missing tools: %s. Installing...", missing)
            self._install_dependencies(missing)
    
    def _install_dependencies(self, tools: List[str]):
        """Install missing dependencies."""
        try:
            subprocess.run(
                ['sudo', 'apt-get', 'install', '-y'] + tools,
                capture_output=True, check=True
            )
        except Exception as e:
            logger.error("Failed to install dependencies: %s", e)
    
    # ── Mouse Control ─────────────────────────────────────────
    
    def move_mouse(self, x: int, y: int) -> bool:
        """Move mouse to absolute coordinates."""
        try:
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
            return True
        except Exception as e:
            logger.error("Mouse move failed: %s", e)
            return False
    
    def click(self, button: int = 1) -> bool:
        """Click at current position. button: 1=left, 2=middle, 3=right."""
        try:
            subprocess.run(['xdotool', 'click', str(button)], check=True)
            return True
        except Exception as e:
            logger.error("Click failed: %s", e)
            return False
    
    def click_at(self, x: int, y: int, button: int = 1) -> bool:
        """Move to position and click."""
        if self.move_mouse(x, y):
            time.sleep(0.1)
            return self.click(button)
        return False
    
    def double_click(self) -> bool:
        """Double click at current position."""
        try:
            subprocess.run(['xdotool', 'click', '--repeat', '2', '1'], check=True)
            return True
        except Exception as e:
            logger.error("Double click failed: %s", e)
            return False
    
    def right_click(self) -> bool:
        """Right click at current position."""
        return self.click(3)
    
    def drag(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Drag from (x1,y1) to (x2,y2)."""
        try:
            subprocess.run(['xdotool', 'mousemove', str(x1), str(y1)], check=True)
            subprocess.run(['xdotool', 'mousedown', '1'], check=True)
            subprocess.run(['xdotool', 'mousemove', str(x2), str(y2)], check=True)
            subprocess.run(['xdotool', 'mouseup', '1'], check=True)
            return True
        except Exception as e:
            logger.error("Drag failed: %s", e)
            return False
    
    def scroll(self, direction: str = "up", amount: int = 5) -> bool:
        """Scroll mouse wheel. direction: 'up' or 'down'."""
        try:
            button = "4" if direction == "up" else "5"
            for _ in range(amount):
                subprocess.run(['xdotool', 'click', button], check=True)
                time.sleep(0.05)
            return True
        except Exception as e:
            logger.error("Scroll failed: %s", e)
            return False
    
    # ── Keyboard Control ──────────────────────────────────────
    
    def type_text(self, text: str, delay: int = 50) -> bool:
        """Type text character by character."""
        try:
            subprocess.run(['xdotool', 'type', '--delay', str(delay), text], check=True)
            return True
        except Exception as e:
            logger.error("Type failed: %s", e)
            return False
    
    def press_key(self, key: str) -> bool:
        """Press a single key (e.g., 'Return', 'Tab', 'Escape')."""
        try:
            subprocess.run(['xdotool', 'key', key], check=True)
            return True
        except Exception as e:
            logger.error("Key press failed: %s", e)
            return False
    
    def hotkey(self, *keys: str) -> bool:
        """Press a key combination (e.g., 'ctrl+c', 'alt+tab')."""
        try:
            combo = '+'.join(keys)
            subprocess.run(['xdotool', 'key', combo], check=True)
            return True
        except Exception as e:
            logger.error("Hotkey failed: %s", e)
            return False
    
    def ctrl_c(self):
        """Copy."""
        return self.hotkey('ctrl', 'c')
    
    def ctrl_v(self):
        """Paste."""
        return self.hotkey('ctrl', 'v')
    
    def ctrl_z(self):
        """Undo."""
        return self.hotkey('ctrl', 'z')
    
    def alt_tab(self):
        """Switch window."""
        return self.hotkey('alt', 'Tab')
    
    def enter(self):
        """Press Enter."""
        return self.press_key('Return')
    
    def escape(self):
        """Press Escape."""
        return self.press_key('Escape')
    
    # ── Window Management ─────────────────────────────────────
    
    def get_active_window(self) -> Optional[int]:
        """Get the active window ID."""
        try:
            result = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True, text=True, check=True
            )
            return int(result.stdout.strip())
        except Exception as e:
            logger.error("Get active window failed: %s", e)
            return None
    
    def find_window(self, title: str) -> Optional[int]:
        """Find a window by title (partial match)."""
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--name', title],
                capture_output=True, text=True, check=True
            )
            windows = result.stdout.strip().split('\n')
            if windows and windows[0]:
                return int(windows[0])
            return None
        except Exception as e:
            logger.error("Find window failed: %s", e)
            return None
    
    def focus_window(self, window_id: int) -> bool:
        """Focus a window by ID."""
        try:
            subprocess.run(['xdotool', 'windowactivate', str(window_id)], check=True)
            return True
        except Exception as e:
            logger.error("Focus window failed: %s", e)
            return False
    
    def resize_window(self, window_id: int, width: int, height: int) -> bool:
        """Resize a window."""
        try:
            subprocess.run(
                ['xdotool', 'windowsize', str(window_id), str(width), str(height)],
                check=True
            )
            return True
        except Exception as e:
            logger.error("Resize window failed: %s", e)
            return False
    
    def move_window(self, window_id: int, x: int, y: int) -> bool:
        """Move a window."""
        try:
            subprocess.run(
                ['xdotool', 'windowmove', str(window_id), str(x), str(y)],
                check=True
            )
            return True
        except Exception as e:
            logger.error("Move window failed: %s", e)
            return False
    
    def minimize_window(self, window_id: int) -> bool:
        """Minimize a window."""
        try:
            subprocess.run(['xdotool', 'windowminimize', str(window_id)], check=True)
            return True
        except Exception as e:
            logger.error("Minimize window failed: %s", e)
            return False
    
    def maximize_window(self, window_id: int) -> bool:
        """Maximize a window."""
        try:
            subprocess.run(
                ['xdotool', 'windowsize', str(window_id), '100%', '100%'],
                check=True
            )
            return True
        except Exception as e:
            logger.error("Maximize window failed: %s", e)
            return False
    
    def close_window(self, window_id: int) -> bool:
        """Close a window."""
        try:
            subprocess.run(['xdotool', 'windowclose', str(window_id)], check=True)
            return True
        except Exception as e:
            logger.error("Close window failed: %s", e)
            return False
    
    def list_windows(self) -> List[Dict[str, Any]]:
        """List all visible windows."""
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--onlyvisible', '--name', ''],
                capture_output=True, text=True, check=True
            )
            windows = []
            for wid in result.stdout.strip().split('\n'):
                if wid:
                    try:
                        name_result = subprocess.run(
                            ['xdotool', 'getwindowname', wid],
                            capture_output=True, text=True
                        )
                        windows.append({
                            'id': int(wid),
                            'name': name_result.stdout.strip()
                        })
                    except:
                        pass
            return windows
        except Exception as e:
            logger.error("List windows failed: %s", e)
            return []
    
    # ── Screenshot ─────────────────────────────────────────────
    
    def screenshot(self, output_path: str = "/tmp/orion_screenshot.png") -> Optional[str]:
        """Take a screenshot of the entire screen."""
        try:
            subprocess.run(['scrot', output_path], check=True)
            logger.info("Screenshot saved: %s", output_path)
            return output_path
        except FileNotFoundError:
            # Fallback to import
            try:
                subprocess.run(['import', '-window', 'root', output_path], check=True)
                return output_path
            except:
                logger.error("Screenshot failed: no tool available")
                return None
        except Exception as e:
            logger.error("Screenshot failed: %s", e)
            return None
    
    def screenshot_window(self, window_id: int, output_path: str = "/tmp/orion_window.png") -> Optional[str]:
        """Take a screenshot of a specific window."""
        try:
            subprocess.run(['scrot', '-u', output_path], check=True)
            return output_path
        except Exception as e:
            logger.error("Window screenshot failed: %s", e)
            return None
    
    # ── Clipboard ──────────────────────────────────────────────
    
    def get_clipboard(self) -> Optional[str]:
        """Get clipboard content."""
        try:
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'],
                                  capture_output=True, text=True, check=True)
            return result.stdout
        except Exception as e:
            logger.error("Get clipboard failed: %s", e)
            return None
    
    def set_clipboard(self, text: str) -> bool:
        """Set clipboard content."""
        try:
            subprocess.run(['xclip', '-selection', 'clipboard'],
                          input=text.encode(), check=True)
            return True
        except Exception as e:
            logger.error("Set clipboard failed: %s", e)
            return False
    
    # ── Mouse Position ─────────────────────────────────────────
    
    def get_mouse_position(self) -> Optional[Tuple[int, int]]:
        """Get current mouse position."""
        try:
            result = subprocess.run(
                ['xdotool', 'getmouselocation'],
                capture_output=True, text=True, check=True
            )
            # Parse output: "x:123 y:456 screen:0 window:789"
            parts = result.stdout.split()
            x = int(parts[0].split(':')[1])
            y = int(parts[1].split(':')[1])
            return (x, y)
        except Exception as e:
            logger.error("Get mouse position failed: %s", e)
            return None
    
    # ── Screen Info ────────────────────────────────────────────
    
    def get_screen_size(self) -> Optional[Tuple[int, int]]:
        """Get screen resolution."""
        try:
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True, text=True, check=True
            )
            for line in result.stdout.split('\n'):
                if 'dimensions:' in line:
                    # Parse: "dimensions:    1920x1080 pixels"
                    dim = line.split(':')[1].strip().split(' ')[0]
                    w, h = dim.split('x')
                    return (int(w), int(h))
            return None
        except Exception as e:
            logger.error("Get screen size failed: %s", e)
            return None
