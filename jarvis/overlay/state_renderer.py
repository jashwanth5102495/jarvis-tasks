
"""
State Renderer Module
====================
Renders overlay state to the PyQt6 UI
"""
import logging
from typing import Optional
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from jarvis.overlay.ui_theme_manager import ui_theme_manager

logger = logging.getLogger(__name__)


class StateRenderer:
    """Renders JARVIS state to the overlay UI."""

    def __init__(self):
        logger.info("StateRenderer initialized")

    def render_status(self, label: QLabel, status: str, details: Optional[str] = None):
        """Render the current status to the label."""
        colors = ui_theme_manager.colors
        status_text = f"🤖 {status}"
        if details:
            status_text += f"\n{details}"

        label.setText(status_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {colors.text};
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }}
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)


# Module-level singleton
state_renderer = StateRenderer()

