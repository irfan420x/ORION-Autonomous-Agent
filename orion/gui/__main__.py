"""
ORION GUI - Main Entry Point
==============================

Launch the ORION Desktop GUI application.

Usage:
    python3 -m orion.gui
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication

from .windows.splash_window import SplashWindow
from .windows.main_window import MainWindow


def main():
    """Launch ORION GUI."""
    # High DPI support
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("ORION")
    app.setApplicationDisplayName("⚡ ORION - Autonomous Intelligence System")
    
    # Dark palette
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#050510"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e6edf3"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#00d4ff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#050510"))
    app.setPalette(palette)
    
    # Global font
    from PyQt6.QtGui import QFont
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Splash screen
    splash = SplashWindow()
    main_window = MainWindow()
    
    def on_splash_done():
        main_window.show()
    
    splash.finished.connect(on_splash_done)
    splash.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
