"""
ORION GUI - Animated AI Core
==============================

Central animated energy sphere with rings, pulses, and states.
"""

import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPen, QBrush

from ..core.theme import Colors


class OrionCore(QWidget):
    """Animated AI core visualization."""
    
    STATE_IDLE = "idle"
    STATE_THINKING = "thinking"
    STATE_LISTENING = "listening"
    STATE_SPEAKING = "speaking"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self._state = self.STATE_IDLE
        self._angle = 0.0
        self._pulse = 0.0
        self._pulse_dir = 1
        self._ring_angles = [0, 60, 120]
        self._particle_phase = 0.0
        
        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)  # ~30 FPS
    
    def set_state(self, state: str):
        self._state = state
        self.update()
    
    def _animate(self):
        self._angle += 2
        if self._angle >= 360:
            self._angle -= 360
        
        self._pulse += 0.03 * self._pulse_dir
        if self._pulse > 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse < 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1
        
        for i in range(len(self._ring_angles)):
            speed = 1.5 if i == 0 else (1.0 if i == 1 else 0.7)
            self._ring_angles[i] += speed
            if self._ring_angles[i] >= 360:
                self._ring_angles[i] -= 360
        
        self._particle_phase += 0.05
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        radius = min(w, h) * 0.3
        
        # Background glow
        glow = QRadialGradient(cx, cy, radius * 2)
        if self._state == self.STATE_THINKING:
            glow.setColorAt(0, QColor(0, 212, 255, 30))
        elif self._state == self.STATE_LISTENING:
            glow.setColorAt(0, QColor(63, 185, 80, 30))
        else:
            glow.setColorAt(0, QColor(0, 212, 255, 15))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius * 2, radius * 2)
        
        # Rotating rings
        for i, ring_angle in enumerate(self._ring_angles):
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(ring_angle)
            
            ring_radius = radius * (1.2 + i * 0.25)
            alpha = 80 - i * 20
            
            pen = QPen(QColor(0, 212, 255, max(20, alpha)))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Draw partial ring (arc)
            start_angle = int(30 * 16)
            span_angle = int(120 * 16)
            painter.drawEllipse(QPointF(0, 0), ring_radius, ring_radius * 0.3)
            painter.restore()
        
        # Core sphere
        core_gradient = QRadialGradient(cx, cy, radius)
        pulse_factor = 0.8 + self._pulse * 0.2
        
        if self._state == self.STATE_THINKING:
            core_gradient.setColorAt(0, QColor(0, 212, 255, int(200 * pulse_factor)))
            core_gradient.setColorAt(0.7, QColor(9, 105, 218, int(150 * pulse_factor)))
            core_gradient.setColorAt(1, QColor(0, 100, 200, int(50 * pulse_factor)))
        elif self._state == self.STATE_LISTENING:
            core_gradient.setColorAt(0, QColor(63, 185, 80, int(200 * pulse_factor)))
            core_gradient.setColorAt(0.7, QColor(40, 150, 60, int(150 * pulse_factor)))
            core_gradient.setColorAt(1, QColor(20, 100, 40, int(50 * pulse_factor)))
        else:
            core_gradient.setColorAt(0, QColor(0, 180, 220, int(180 * pulse_factor)))
            core_gradient.setColorAt(0.7, QColor(0, 100, 180, int(120 * pulse_factor)))
            core_gradient.setColorAt(1, QColor(0, 60, 120, int(40 * pulse_factor)))
        
        painter.setBrush(QBrush(core_gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius * pulse_factor, radius * pulse_factor)
        
        # Inner highlight
        highlight = QRadialGradient(cx - radius * 0.2, cy - radius * 0.2, radius * 0.5)
        highlight.setColorAt(0, QColor(255, 255, 255, 40))
        highlight.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(QPointF(cx, cy), radius * 0.8, radius * 0.8)
        
        # Particles
        for i in range(8):
            angle = (self._particle_phase + i * 0.8) % (2 * math.pi)
            dist = radius * (1.5 + 0.3 * math.sin(self._particle_phase * 2 + i))
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            size = 2 + math.sin(self._particle_phase + i) * 1
            
            painter.setBrush(QBrush(QColor(0, 212, 255, 120)))
            painter.drawEllipse(QPointF(px, py), size, size)
        
        # Center text
        painter.setPen(QColor(255, 255, 255, 200))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        if self._state == self.STATE_THINKING:
            text = "THINKING..."
        elif self._state == self.STATE_LISTENING:
            text = "LISTENING..."
        elif self._state == self.STATE_SPEAKING:
            text = "SPEAKING..."
        else:
            text = "ORION"
        
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
