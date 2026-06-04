
"""
notification_manager.py
========================
Notification handling for JARVIS UI.
Shows subtle notifications without being intrusive.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationManager:
    def __init__(self):
        logger.info("Notification Manager initialized")
        self._notification_queue: list = []

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show a desktop notification"""
        logger.info(f"Notification: {title} - {message}")
        try:
            from PyQt6.QtWidgets import QSystemTrayIcon, QMessageBox
            from PyQt6.QtGui import QIcon
            # For now we just log it - will integrate with tray later
        except ImportError:
            logger.warning("PyQt6 not available for notifications")

    def queue_notification(self, title: str, message: str):
        """Queue a notification to be shown later"""
        self._notification_queue.append((title, message))


notification_manager = NotificationManager()

