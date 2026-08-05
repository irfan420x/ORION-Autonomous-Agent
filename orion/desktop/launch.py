#!/usr/bin/env python3
"""
ORION Desktop Application Launcher
====================================
Launches the ORION GUI desktop application.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from orion.desktop.app import OrionDesktopApp

if __name__ == "__main__":
    print("⚡ Starting ORION Desktop GUI...")
    app = OrionDesktopApp()
    app.run()
