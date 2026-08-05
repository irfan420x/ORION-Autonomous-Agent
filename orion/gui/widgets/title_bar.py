"""
ORION GUI - Custom Title Bar
=============================

Borderless window title bar with drag, minimize, maximize, close.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont

from ..core.theme import Colors, Theme


class TitleBar(QWidget):
    """Custom draggable title bar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self._drag_pos = None
        self.setObjectName("titleBar")
        self.setFixedHeight(40)
        self.setStyleSheet(Theme.TITLE_BAR)
        self._build_ui()
    
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # App name
        self.title = QLabel("⚡ ORION")
        self.title.setStyleSheet(f"""
            color: {Colors.CYAN};
            font-size: 14px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.title)
        
        layout.addStretch()
        
        # Subtitle
        subtitle = QLabel("AUTONOMOUS INTELLIGENCE SYSTEM")
        subtitle.setStyleSheet(f"""
            color: {Colors.GRAY};
            font-size: 9px;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        # Window controls
        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.GRAY};
                font-size: 16px;
                width: 36px;
                height: 36px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {Colors.BG_CARD};
                color: {Colors.WHITE};
            }}
        """
        
        close_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.GRAY};
                font-size: 16px;
                width: 36px;
                height: 36px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {Colors.RED};
                color: {Colors.WHITE};
            }}
        """
        
        self.btn_min = QPushButton("─")
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(self._minimize)
        
        self.btn_max = QPushButton("□")
        self.btn_max.setStyleSheet(btn_style)
        self.btn_max.clicked.connect(self._maximize)
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setStyleSheet(close_style)
        self.btn_close.clicked.connect(self._close)
        
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent.pos()
    
    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    
    def mouseDoubleClickEvent(self, event):
        self._maximize()
    
    def _minimize(self):
        self.parent.showMinimized()
    
    def _maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()
    
    def _close(self):
        self.parent.close()
