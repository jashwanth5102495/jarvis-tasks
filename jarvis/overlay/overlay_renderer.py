
"""
overlay_renderer.py
===================
Rendering logic for JARVIS cinematic overlay.
Handles positioning, sizing, and visual rendering.
"""

import logging
from typing import Optional, Tuple
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPoint

logger = logging.getLogger(__name__)


class OverlayRenderer:
    def __init__(self):
        self._position: str = "top-right"
        self._offset: Tuple[int, int] = (20, 20)
        logger.info("Overlay Renderer initialized")

    def calculate_position(self, screen_width: int, screen_height: int,
                           widget_width: int, widget_height: int) -> QPoint:
        """Calculate widget position based on current settings"""
        x, y = self._offset

        if self._position == "top-right":
            x = screen_width - widget_width - x
        elif self._position == "top-left":
            x = x
        elif self._position == "bottom-right":
            x = screen_width - widget_width - x
            y = screen_height - widget_height - y
        elif self._position == "bottom-left":
            x = x
            y = screen_height - widget_height - y

        return QPoint(x, y)

    def get_screen_geometry(self):
        """Get primary screen geometry"""
        if QApplication.instance():
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.geometry()
                available = screen.availableGeometry()
                logger.info(f"Screen geometry: {geom}, available: {available}")
                return geom
        return None

    def set_position(self, position: str, offset: Optional[Tuple[int, int]] = None):
        """Set overlay position"""
        valid_positions = ["top-right", "top-left", "bottom-right", "bottom-left"]
        if position in valid_positions:
            self._position = position
            if offset:
                self._offset = offset
            logger.info(f"Overlay position set to {position} with offset {self._offset}")
        else:
            logger.warning(f"Invalid position: {position}")


overlay_renderer = OverlayRenderer()

