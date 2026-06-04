
"""
STANDALONE OVERLAY TEST - NO JARVIS RUNTIME!
Just shows a red box at 100, 100!
"""
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont


class SimpleOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        print("OVERLAY INITIALIZED")

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setMinimumSize(400, 100)
        self.resize(400, 100)

        layout = QVBoxLayout()
        label = QLabel("STANDALONE TEST OVERLAY!")
        label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white;")
        layout.addWidget(label)
        self.setLayout(layout)
        self.move(100, 100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 0, 0, 255))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("CREATING APP")
    overlay = SimpleOverlay()
    print("SHOWING OVERLAY")
    overlay.show()
    overlay.raise_()
    overlay.activateWindow()
    print("OVERLAY VISIBLE:", overlay.isVisible())
    sys.exit(app.exec())
