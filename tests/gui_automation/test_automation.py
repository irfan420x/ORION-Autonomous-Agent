"""
Tests for ORION GUI Automation (M5.2)
======================================
"""

import pytest
from unittest.mock import patch, MagicMock

from orion.gui_automation.automation import GUIAutomation


@pytest.fixture
def auto():
    with patch.object(GUIAutomation, '_check_dependencies'):
        return GUIAutomation()


class TestGUIAutomation:
    def test_initialization(self, auto):
        assert auto is not None

    @patch('subprocess.run')
    def test_move_mouse(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.move_mouse(100, 200) is True
        mock_run.assert_called_with(['xdotool', 'mousemove', '100', '200'], check=True)

    @patch('subprocess.run')
    def test_click(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.click(1) is True
        mock_run.assert_called_with(['xdotool', 'click', '1'], check=True)

    @patch('subprocess.run')
    def test_click_at(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.click_at(100, 200) is True

    @patch('subprocess.run')
    def test_type_text(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.type_text("Hello") is True

    @patch('subprocess.run')
    def test_press_key(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.press_key("Return") is True

    @patch('subprocess.run')
    def test_hotkey(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.hotkey('ctrl', 'c') is True

    @patch('subprocess.run')
    def test_scroll(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.scroll("up", 3) is True

    @patch('subprocess.run')
    def test_drag(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.drag(10, 20, 100, 200) is True

    @patch('subprocess.run')
    def test_get_active_window(self, mock_run, auto):
        mock_run.return_value = MagicMock(stdout="12345\n", returncode=0)
        assert auto.get_active_window() == 12345

    @patch('subprocess.run')
    def test_find_window(self, mock_run, auto):
        mock_run.return_value = MagicMock(stdout="12345\n", returncode=0)
        assert auto.find_window("Firefox") == 12345

    @patch('subprocess.run')
    def test_focus_window(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.focus_window(12345) is True

    @patch('subprocess.run')
    def test_list_windows(self, mock_run, auto):
        mock_run.return_value = MagicMock(stdout="12345\n67890\n", returncode=0)
        windows = auto.list_windows()
        assert isinstance(windows, list)

    @patch('subprocess.run')
    def test_screenshot(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        result = auto.screenshot("/tmp/test.png")
        assert result == "/tmp/test.png"

    @patch('subprocess.run')
    def test_get_mouse_position(self, mock_run, auto):
        mock_run.return_value = MagicMock(stdout="x:100 y:200 screen:0", returncode=0)
        pos = auto.get_mouse_position()
        assert pos == (100, 200)

    @patch('subprocess.run')
    def test_get_screen_size(self, mock_run, auto):
        mock_run.return_value = MagicMock(stdout="dimensions:    1920x1080 pixels", returncode=0)
        size = auto.get_screen_size()
        assert size == (1920, 1080)

    @patch('subprocess.run')
    def test_set_clipboard(self, mock_run, auto):
        mock_run.return_value = MagicMock(returncode=0)
        assert auto.set_clipboard("test") is True

    def test_convenience_methods(self, auto):
        with patch.object(auto, 'hotkey', return_value=True):
            assert auto.ctrl_c() is True
            assert auto.ctrl_v() is True
            assert auto.ctrl_z() is True
            assert auto.alt_tab() is True
        
        with patch.object(auto, 'press_key', return_value=True):
            assert auto.enter() is True
            assert auto.escape() is True
