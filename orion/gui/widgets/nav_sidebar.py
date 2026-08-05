"""
ORION GUI - Navigation Sidebar
===============================

Left sidebar with navigation items, voice status, system health.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer
from PyQt6.QtGui import QFont

from ..core.theme import Colors, Theme
from ..core.signals import get_signal_bus


class NavSidebar(QWidget):
    """Left navigation sidebar."""
    
    page_requested = Signal(str)
    
    NAV_ITEMS = [
        ("dashboard", "📊", "DASHBOARD"),
        ("agent", "🤖", "AGENT"),
        ("tasks", "📋", "TASKS"),
        ("memory", "🧠", "MEMORY"),
        ("knowledge", "📚", "KNOWLEDGE"),
        ("world", "🌐", "WORLD MODEL"),
        ("planner", "📐", "PLANNER"),
        ("reasoning", "💡", "REASONING"),
        ("terminal", "💻", "TERMINAL"),
        ("files", "📁", "FILES"),
        ("extensions", "🧩", "EXTENSIONS"),
        ("logs", "📝", "LOGS"),
        ("system", "⚙️", "SYSTEM"),
        ("settings", "🔧", "SETTINGS"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self.setStyleSheet(Theme.SIDEBAR)
        self._buttons = {}
        self._current = "dashboard"
        self._build_ui()
        self._connect_signals()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(0)
        
        # Navigation buttons
        for page_id, icon, label in self.NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setStyleSheet(Theme.NAV_BUTTON)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_nav_click(pid))
            self._buttons[page_id] = btn
            layout.addWidget(btn)
        
        # Set dashboard as active
        self._buttons["dashboard"].setChecked(True)
        
        layout.addStretch()
        
        # Voice Status
        voice_frame = QFrame()
        voice_frame.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                margin: 0 10px;
                padding: 10px;
            }}
        """)
        voice_layout = QVBoxLayout(voice_frame)
        
        voice_icon = QLabel("🎙️")
        voice_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        voice_icon.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        voice_layout.addWidget(voice_icon)
        
        self.voice_label = QLabel("Listening...")
        self.voice_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.voice_label.setStyleSheet(f"""
            color: {Colors.GREEN};
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        voice_layout.addWidget(self.voice_label)
        
        layout.addWidget(voice_frame)
        
        # System Health
        health_frame = QFrame()
        health_frame.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                margin: 10px 10px;
                padding: 10px;
            }}
        """)
        health_layout = QVBoxLayout(health_frame)
        
        health_title = QLabel("SYSTEM HEALTH")
        health_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        health_title.setStyleSheet(f"""
            color: {Colors.GRAY};
            font-size: 8px;
            font-weight: bold;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        health_layout.addWidget(health_title)
        
        self.health_value = QLabel("98%")
        self.health_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_value.setStyleSheet(f"""
            color: {Colors.GREEN};
            font-size: 28px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        health_layout.addWidget(self.health_value)
        
        self.health_status = QLabel("All Systems Operational")
        self.health_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_status.setStyleSheet(f"""
            color: {Colors.GREEN};
            font-size: 9px;
            background: transparent;
            border: none;
        """)
        health_layout.addWidget(self.health_status)
        
        layout.addWidget(health_frame)
    
    def _connect_signals(self):
        bus = get_signal_bus()
        bus.system_health.connect(self._update_health)
        bus.voice_listening.connect(self._update_voice)
    
    def _on_nav_click(self, page_id: str):
        # Uncheck all buttons
        for btn in self._buttons.values():
            btn.setChecked(False)
        
        # Check clicked button
        self._buttons[page_id].setChecked(True)
        self._current = page_id
        self.page_requested.emit(page_id)
    
    def _update_health(self, value: float):
        self.health_value.setText(f"{value:.0f}%")
        if value >= 90:
            color = Colors.GREEN
            status = "All Systems Operational"
        elif value >= 70:
            color = Colors.ORANGE
            status = "Some Issues Detected"
        else:
            color = Colors.RED
            status = "Critical Issues"
        
        self.health_value.setStyleSheet(f"""
            color: {color};
            font-size: 28px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        self.health_status.setText(status)
        self.health_status.setStyleSheet(f"""
            color: {color};
            font-size: 9px;
            background: transparent;
            border: none;
        """)
    
    def _update_voice(self, listening: bool):
        if listening:
            self.voice_label.setText("Listening...")
            self.voice_label.setStyleSheet(f"color: {Colors.GREEN}; font-size: 10px; background: transparent; border: none;")
        else:
            self.voice_label.setText("Voice Off")
            self.voice_label.setStyleSheet(f"color: {Colors.GRAY}; font-size: 10px; background: transparent; border: none;")
