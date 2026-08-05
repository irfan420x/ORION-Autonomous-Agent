"""
ORION GUI - Main Window
========================

Borderless main window with sidebar, pages, dock.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from ..core.theme import Colors, Sizes, Theme
from ..core.signals import get_signal_bus
from ..widgets.title_bar import TitleBar
from ..widgets.nav_sidebar import NavSidebar
from ..pages.dashboard_page import DashboardPage


class CommandDock(QFrame):
    """Bottom application dock."""
    
    APPS = [
        ("💻", "Terminal"), ("🌐", "Browser"), ("📝", "Code"), ("📁", "Files"),
        ("⚡", "ORION"), ("📋", "Notes"), ("📅", "Calendar"), ("🎵", "Music"), ("💬", "Chat"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SECONDARY};
                border-top: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(8)
        
        for icon, label in self.APPS:
            btn = QPushButton(icon)
            btn.setToolTip(label)
            btn.setStyleSheet(Theme.DOCK_BUTTON)
            btn.setFixedSize(48, 48)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, l=label: self._open_app(l))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Chat input
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("How can I help you, Irfan?")
        self.chat_input.setStyleSheet(Theme.INPUT_FIELD)
        self.chat_input.setMinimumWidth(300)
        self.chat_input.returnPressed.connect(self._send_message)
        layout.addWidget(self.chat_input)
        
        # Mic button
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(40, 40)
        self.mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.CYAN};
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {Colors.BLUE};
            }}
        """)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.mic_btn)
    
    def _open_app(self, app: str):
        import subprocess
        if app == "Terminal":
            subprocess.Popen(["x-terminal-emulator"])
        elif app == "Files":
            subprocess.Popen(["xdg-open", "/home/irfan"])
        elif app == "Browser":
            subprocess.Popen(["xdg-open", "https://google.com"])
    
    def _send_message(self):
        text = self.chat_input.text().strip()
        if text:
            bus = get_signal_bus()
            bus.user_message.emit(text)
            self.chat_input.clear()


class MainWindow(QMainWindow):
    """Main borderless application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ ORION")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(1000, 600)
        self.resize(Sizes.WINDOW_WIDTH, Sizes.WINDOW_HEIGHT)
        
        # Center on screen
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - Sizes.WINDOW_WIDTH) // 2,
            (screen.height() - Sizes.WINDOW_HEIGHT) // 2
        )
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {Colors.BG_PRIMARY};
            }}
            QStackedWidget {{
                background: transparent;
            }}
        """)
        
        self._build_ui()
        self._connect_signals()
    
    def _build_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Title bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        # Content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = NavSidebar()
        content_layout.addWidget(self.sidebar)
        
        # Pages stack
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background: transparent;")
        
        # Create pages
        self.dashboard_page = DashboardPage()
        self.pages.addWidget(self.dashboard_page)
        
        # Placeholder pages
        for page_name in ["Agent", "Tasks", "Memory", "Knowledge", "World Model",
                         "Planner", "Reasoning", "Terminal", "Files", "Extensions",
                         "Logs", "System", "Settings"]:
            placeholder = QWidget()
            from PyQt6.QtWidgets import QLabel
            label = QLabel(f"🚧 {page_name} - Coming Soon")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {Colors.GRAY}; font-size: 18px;")
            layout = QVBoxLayout(placeholder)
            layout.addWidget(label)
            self.pages.addWidget(placeholder)
        
        content_layout.addWidget(self.pages, 1)
        
        main_layout.addWidget(content, 1)
        
        # Command dock
        self.dock = CommandDock()
        main_layout.addWidget(self.dock)
    
    def _connect_signals(self):
        self.sidebar.page_requested.connect(self._switch_page)
        
        bus = get_signal_bus()
        bus.user_message.connect(self._handle_message)
    
    def _switch_page(self, page_id: str):
        page_map = {
            "dashboard": 0, "agent": 1, "tasks": 2, "memory": 3,
            "knowledge": 4, "world": 5, "planner": 6, "reasoning": 7,
            "terminal": 8, "files": 9, "extensions": 10, "logs": 11,
            "system": 12, "settings": 13,
        }
        index = page_map.get(page_id, 0)
        self.pages.setCurrentIndex(index)
    
    def _handle_message(self, text: str):
        """Handle user message from dock input."""
        print(f"User message: {text}")
        # TODO: Send to LLM
