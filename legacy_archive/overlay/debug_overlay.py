
"""
debug_overlay.py
================
Debug tool for testing JARVIS overlay states and animations.
Provides a simple GUI to switch between different statuses and preview effects.
"""

import sys
import logging

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QComboBox, QHBoxLayout
)
from PyQt6.QtCore import Qt

from runtime.runtime_state import RuntimeStatus
from overlay.ai_indicator import AIIndicator

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class DebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS Overlay Debugger")
        self.setGeometry(100, 100, 400, 300)
        
        # Create main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title label
        title_label = QLabel("JARVIS Cinematic Overlay Debugger")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status selector
        status_layout = QHBoxLayout()
        status_label = QLabel("Select Status:")
        self.status_combo = QComboBox()
        for status in RuntimeStatus:
            self.status_combo.addItem(status.name, status)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_combo)
        layout.addLayout(status_layout)
        
        # Apply status button
        apply_btn = QPushButton("Apply Status")
        apply_btn.clicked.connect(self._apply_status)
        layout.addWidget(apply_btn)
        
        # Info label
        info_label = QLabel("Use this tool to test all overlay states and animations!")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-top: 15px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Add stretch to push everything up
        layout.addStretch()
        
        # Create and show the overlay
        self.overlay = AIIndicator()
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()

    def _apply_status(self):
        status = self.status_combo.currentData()
        self.overlay.set_status(status)


def main():
    app = QApplication(sys.argv)
    window = DebugWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
