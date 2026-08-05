"""
ORION GUI - Splash Window
==========================

Boot sequence splash screen with animation.
"""

import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QFont

from ..core.theme import Colors


class SplashWindow(QWidget):
    """Splash screen with boot animation."""
    
    finished = Signal()
    
    BOOT_STEPS = [
        (10, "Initializing ORION Core..."),
        (20, "Loading AI Engine..."),
        (30, "Loading Memory System..."),
        (40, "Loading Knowledge Base..."),
        (50, "Loading World Model..."),
        (60, "Loading Plugins..."),
        (70, "Loading Voice System..."),
        (80, "Loading Services..."),
        (90, "Running System Check..."),
        (100, "System Ready"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 400)
        
        # Center on screen
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - 600) // 2,
            (screen.height() - 400) // 2
        )
        
        self._progress = 0
        self._status = ""
        self._step_index = 0
        self._angle = 0
        self._pulse = 0
        self._pulse_dir = 1
        
        self._build_ui()
        self._start_boot()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Logo
        self.logo = QLabel("⚡")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setStyleSheet("font-size: 72px; background: transparent;")
        layout.addWidget(self.logo)
        
        # Title
        self.title = QLabel("ORION")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(f"""
            color: {Colors.CYAN};
            font-size: 36px;
            font-weight: bold;
            letter-spacing: 8px;
            background: transparent;
        """)
        layout.addWidget(self.title)
        
        # Subtitle
        self.subtitle = QLabel("AUTONOMOUS INTELLIGENCE SYSTEM")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet(f"""
            color: {Colors.GRAY};
            font-size: 10px;
            letter-spacing: 4px;
            background: transparent;
        """)
        layout.addWidget(self.subtitle)
        
        layout.addSpacing(30)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.BORDER};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.CYAN_DIM}, stop:1 {Colors.CYAN});
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {Colors.GRAY};
            font-size: 11px;
            background: transparent;
        """)
        layout.addWidget(self.status_label)
    
    def _start_boot(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._boot_step)
        self._timer.start(300)
        
        # Animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(33)
    
    def _boot_step(self):
        if self._step_index >= len(self.BOOT_STEPS):
            self._timer.stop()
            QTimer.singleShot(500, self._finish)
            return
        
        progress, status = self.BOOT_STEPS[self._step_index]
        self._progress = progress
        self._status = status
        
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
        self._step_index += 1
    
    def _animate(self):
        self._angle += 3
        if self._angle >= 360:
            self._angle -= 360
        
        self._pulse += 0.05 * self._pulse_dir
        if self._pulse > 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse < 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1
        
        self.update()
    
    def _finish(self):
        self._anim_timer.stop()
        self.finished.emit()
        self.close()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.setBrush(QColor(5, 5, 16, 240))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)
        
        # Border
        from PyQt6.QtGui import QPen
        pen = QPen(QColor(0, 212, 255, 60), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 16, 16)
        
        # Glow behind logo
        cx = self.width() / 2
        cy = 140
        glow = QRadialGradient(cx, cy, 100)
        alpha = int(20 + self._pulse * 20)
        glow.setColorAt(0, QColor(0, 212, 255, alpha))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(int(cx - 100), int(cy - 100), 200, 200)
        
        painter.end()
