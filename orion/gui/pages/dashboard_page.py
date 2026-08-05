"""
ORION GUI - Dashboard Page
===========================

Main dashboard with system overview, tasks, memory, actions.
"""

import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal
from PyQt6.QtGui import QFont

from ..core.theme import Colors, Theme
from ..core.signals import get_signal_bus
from ..widgets.orion_core import OrionCore


class Card(QFrame):
    """Reusable card widget."""
    
    def __init__(self, title: str, badge_text: str = "", badge_color: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(Theme.CARD)
        self.setMinimumHeight(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet(Theme.LABEL_SECONDARY)
        header.addWidget(title_label)
        
        header.addStretch()
        
        if badge_text:
            badge = QLabel(badge_text)
            if badge_color == "green":
                badge.setStyleSheet(Theme.BADGE_GREEN)
            elif badge_color == "orange":
                badge.setStyleSheet(Theme.BADGE_ORANGE)
            else:
                badge.setStyleSheet(Theme.BADGE_GREEN)
            header.addWidget(badge)
        
        layout.addLayout(header)
        
        # Content area
        self.content = QVBoxLayout()
        layout.addLayout(self.content)
        layout.addStretch()


class GaugeWidget(QWidget):
    """Circular gauge widget."""
    
    def __init__(self, label: str = "HEALTH", parent=None):
        super().__init__(parent)
        self._value = 100
        self._label = label
        self.setFixedSize(140, 140)
    
    def set_value(self, value: float):
        self._value = min(100, max(0, value))
        self.update()
    
    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient, QBrush
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.width() / 2
        cy = self.height() / 2
        radius = 55
        
        # Background ring
        pen = QPen(QColor(Colors.BORDER), 8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))
        
        # Value ring
        color = QColor(Colors.CYAN) if self._value >= 70 else (QColor(Colors.ORANGE) if self._value >= 40 else QColor(Colors.RED))
        pen.setColor(color)
        painter.setPen(pen)
        
        span = int(self._value / 100 * 360 * 16)
        painter.drawArc(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2), 90 * 16, -span)
        
        # Center text
        painter.setPen(QColor(Colors.WHITE))
        font = painter.font()
        font.setPointSize(22)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}%")
        
        # Label
        painter.setPen(QColor(Colors.GRAY))
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        from PyQt6.QtCore import QRect
        label_rect = QRect(0, int(cy + 15), self.width(), 20)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._label)
        
        painter.end()


class ResourceBar(QWidget):
    """Resource usage bar."""
    
    def __init__(self, icon: str, name: str, parent=None):
        super().__init__(parent)
        self._value = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        icon_label.setFixedWidth(25)
        layout.addWidget(icon_label)
        
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {Colors.WHITE}; font-size: 11px; background: transparent; border: none;")
        name_label.setFixedWidth(70)
        layout.addWidget(name_label)
        
        self.bar_frame = QFrame()
        self.bar_frame.setStyleSheet(f"background: {Colors.BORDER}; border: none; border-radius: 3px;")
        self.bar_frame.setFixedHeight(8)
        layout.addWidget(self.bar_frame, 1)
        
        self.bar_fill = QFrame(self.bar_frame)
        self.bar_fill.setStyleSheet(f"background: {Colors.CYAN}; border: none; border-radius: 3px;")
        self.bar_fill.setFixedHeight(8)
        
        self.value_label = QLabel("0%")
        self.value_label.setStyleSheet(f"color: {Colors.CYAN}; font-size: 11px; background: transparent; border: none;")
        self.value_label.setFixedWidth(50)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.value_label)
    
    def set_value(self, value: float):
        self._value = value
        self.value_label.setText(f"{value:.1f}%")
        
        # Update bar width
        max_width = self.bar_frame.width()
        self.bar_fill.setGeometry(0, 0, int(max_width * value / 100), 8)
        
        # Update color
        if value >= 80:
            color = Colors.RED
        elif value >= 60:
            color = Colors.ORANGE
        else:
            color = Colors.CYAN
        self.bar_fill.setStyleSheet(f"background: {color}; border: none; border-radius: 3px;")
        self.value_label.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; border: none;")


class DashboardPage(QWidget):
    """Main dashboard page."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._start_updates()
    
    def _build_ui(self):
        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        main_layout = QGridLayout(content)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Card 1: System Overview
        sys_card = Card("📊 SYSTEM OVERVIEW", "OPTIMAL", "green")
        self.gauge = GaugeWidget("HEALTH")
        sys_card.content.addWidget(self.gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.resource_bars = {}
        for icon, name in [("💻", "CPU"), ("🧠", "MEMORY"), ("💾", "DISK")]:
            bar = ResourceBar(icon, name)
            sys_card.content.addWidget(bar)
            self.resource_bars[name] = bar
        
        main_layout.addWidget(sys_card, 0, 0)
        
        # Card 2: Active Tasks
        task_card = Card("📋 ACTIVE TASKS", "3 Active", "orange")
        
        tasks = [
            ("Build ORION World Model", 65, Colors.BLUE),
            ("Analyze Codebase", 40, Colors.BLUE),
            ("Update Documentation", 10, Colors.ORANGE),
            ("Backup System", 0, Colors.ORANGE),
        ]
        
        for task_name, progress, color in tasks:
            task_widget = QWidget()
            task_layout = QHBoxLayout(task_widget)
            task_layout.setContentsMargins(0, 4, 0, 4)
            
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent; border: none;")
            dot.setFixedWidth(15)
            task_layout.addWidget(dot)
            
            info = QVBoxLayout()
            name_label = QLabel(task_name)
            name_label.setStyleSheet(f"color: {Colors.WHITE}; font-size: 11px; background: transparent; border: none;")
            info.addWidget(name_label)
            
            progress_bar = QProgressBar()
            progress_bar.setValue(progress)
            progress_bar.setStyleSheet(Theme.PROGRESS_BAR)
            progress_bar.setFixedHeight(4)
            info.addWidget(progress_bar)
            
            task_layout.addLayout(info, 1)
            
            pct = QLabel(f"{progress}%")
            pct.setStyleSheet(f"color: {Colors.GRAY}; font-size: 11px; background: transparent; border: none;")
            task_layout.addWidget(pct)
            
            task_card.content.addWidget(task_widget)
        
        main_layout.addWidget(task_card, 0, 1)
        
        # Card 3: Memory Status
        mem_card = Card("🧠 MEMORY STATUS", "Active", "green")
        
        mem_grid = QGridLayout()
        mem_grid.setSpacing(10)
        
        mem_stats = [
            ("12,458", "Memories"), ("3,256", "Entities"),
            ("128", "Sessions"), ("89%", "Knowledge Base"),
        ]
        
        for i, (value, label) in enumerate(mem_stats):
            stat_frame = QFrame()
            stat_frame.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.BG_PRIMARY};
                    border: none;
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
            stat_layout = QVBoxLayout(stat_frame)
            
            val = QLabel(value)
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val.setStyleSheet(f"color: {Colors.PURPLE}; font-size: 20px; font-weight: bold; background: transparent; border: none;")
            stat_layout.addWidget(val)
            
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {Colors.GRAY}; font-size: 9px; background: transparent; border: none;")
            stat_layout.addWidget(lbl)
            
            mem_grid.addWidget(stat_frame, i // 2, i % 2)
        
        mem_card.content.addLayout(mem_grid)
        main_layout.addWidget(mem_card, 0, 2)
        
        # Card 4: ORION Core
        core_card = Card("⚡ ORION CORE")
        self.orion_core = OrionCore()
        core_card.content.addWidget(self.orion_core, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(core_card, 1, 0)
        
        # Card 5: Quick Actions
        action_card = Card("⚡ QUICK ACTIONS")
        
        actions_grid = QGridLayout()
        actions_grid.setSpacing(8)
        
        actions = [
            ("🚀", "Launch"), ("🔍", "Search"), ("💻", "Terminal"), ("📝", "Notes"),
            ("🎙️", "Voice"), ("📸", "Screenshot"), ("📁", "Files"), ("📈", "Monitor"),
        ]
        
        for i, (icon, label) in enumerate(actions):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.BG_PRIMARY};
                    color: {Colors.WHITE};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {Colors.BG_CARD_HOVER};
                    border: 1px solid {Colors.CYAN_DIM};
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, a=label: self._action_click(a))
            actions_grid.addWidget(btn, i // 4, i % 4)
        
        action_card.content.addLayout(actions_grid)
        main_layout.addWidget(action_card, 1, 1)
        
        # Card 6: Process Monitor
        proc_card = Card("📈 SYSTEM MONITOR")
        
        self.process_labels = []
        self.process_container = QVBoxLayout()
        proc_card.content.addLayout(self.process_container)
        
        main_layout.addWidget(proc_card, 1, 2)
        
        # Set grid weights
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnStretch(2, 1)
        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 1)
        
        scroll.setWidget(content)
        
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
    
    def _start_updates(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_system)
        self._timer.start(2000)
        self._update_system()
    
    def _update_system(self):
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.resource_bars["CPU"].set_value(cpu)
        self.resource_bars["MEMORY"].set_value(mem.percent)
        self.resource_bars["DISK"].set_value(disk.percent)
        
        health = 100 - max(cpu, mem.percent, disk.percent)
        self.gauge.set_value(health)
        
        # Update processes
        self._update_processes()
        
        # Emit signals
        bus = get_signal_bus()
        bus.cpu_changed.emit(cpu)
        bus.ram_changed.emit(mem.percent)
        bus.disk_changed.emit(disk.percent)
        bus.system_health.emit(health)
    
    def _update_processes(self):
        # Clear old
        for label in self.process_labels:
            label.deleteLater()
        self.process_labels.clear()
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] and pinfo['cpu_percent'] > 0:
                    processes.append(pinfo)
            except:
                pass
        
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        
        for proc in processes[:5]:
            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background: transparent;
                    border-bottom: 1px solid {Colors.BORDER};
                    padding: 4px;
                }}
            """)
            layout = QHBoxLayout(frame)
            layout.setContentsMargins(0, 4, 0, 4)
            
            pid = QLabel(str(proc['pid']))
            pid.setStyleSheet(f"color: {Colors.GRAY}; font-size: 11px; background: transparent; border: none;")
            pid.setFixedWidth(50)
            layout.addWidget(pid)
            
            name = QLabel(proc['name'][:15])
            name.setStyleSheet(f"color: {Colors.WHITE}; font-size: 11px; background: transparent; border: none;")
            layout.addWidget(name, 1)
            
            cpu = QLabel(f"{proc.get('cpu_percent', 0):.1f}%")
            cpu.setStyleSheet(f"color: {Colors.CYAN}; font-size: 11px; background: transparent; border: none;")
            cpu.setFixedWidth(50)
            cpu.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(cpu)
            
            mem = QLabel(f"{proc.get('memory_percent', 0):.1f}%")
            mem.setStyleSheet(f"color: {Colors.GREEN}; font-size: 11px; background: transparent; border: none;")
            mem.setFixedWidth(50)
            mem.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(mem)
            
            self.process_container.addWidget(frame)
            self.process_labels.append(frame)
    
    def _action_click(self, action: str):
        import subprocess
        if action == "Terminal":
            subprocess.Popen(["x-terminal-emulator"])
        elif action == "Files":
            subprocess.Popen(["xdg-open", "/home/irfan"])
        elif action == "Search":
            subprocess.Popen(["xdg-open", "https://google.com"])
