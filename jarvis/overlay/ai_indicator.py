
"""
ai_indicator.py
==============
Glassmorphism PyQt6 overlay for JARVIS AI Operating System.
"""
import logging
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient, QBrush

logger = logging.getLogger(__name__)


class AIIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_text = "🤖 Personal A.I Active\nStatus: Awaiting Commands"
        self._opacity = 0.95

        self._setup_ui()
        logger.info("Glassmorphism AI Indicator initialized")

    def _setup_ui(self):
        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Set fixed size
        self.setMinimumSize(380, 120)
        self.resize(380, 120)

        # Layout and label
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self._label = QLabel(self._status_text)
        self._label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: white;")
        layout.addWidget(self._label)

        # Position top-right initially
        self._position_indicator()

    def _position_indicator(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geometry = screen.availableGeometry()
        x = geometry.width() - self.width() - 30
        y = 30
        self.move(x, y)

    def set_status(self, status, details=None):
        logger.info(f"Setting status to {status} with details: {details}")
        state_map = {
            "IDLE": "🤖 Personal A.I Active\nStatus: Awaiting Commands",
            "PAUSED": "🤖 Personal A.I Paused\nCTRL+P to Resume",
            "LISTENING": "🤖 Listening...",
            "SPEAKING": "🤖 Speaking...",
            "THINKING": "🤖 Thinking...",
            "EXECUTING": "🤖 Executing Workflow...",
            "RECOVERING": "🤖 Recovering Runtime..."
        }
        if hasattr(status, 'name'):
            status_name = status.name
        else:
            status_name = str(status)

        self._status_text = state_map.get(status_name, "🤖 Personal A.I Active")
        if details:
            self._status_text += f"\n{details}"
        self._label.setText(self._status_text)
        self.update()
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw glassmorphism background
        radius = 20
        bg_color = QColor(20, 30, 50, 200)

        # Draw rounded rect
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), radius, radius)

        # Draw cyan glow border
        border_gradient = QLinearGradient(0, 0, self.width(), self.height())
        border_gradient.setColorAt(0, QColor(0, 255, 255, 100))
        border_gradient.setColorAt(1, QColor(0, 150, 200, 100))
        painter.setPen(QColor(0, 200, 255, 150))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), radius, radius)

    def fade_in(self, duration=500):
        self.show()
        animation = QPropertyAnimation(self, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(0.95)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        self.raise_()

    def fade_out(self, duration=500):
        pass  # Overlay should never disappear!

    def stop_animations(self):
        pass

    def start_pulse(self, color, speed):
        pass

    def start_breathing(self, color, speed):
        pass

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    def ensure_visible(self):
        if not self.isVisible():
            self.show()
        self._position_indicator()
        self.raise_()

