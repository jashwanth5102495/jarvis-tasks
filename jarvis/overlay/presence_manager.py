
"""
presence_manager.py
====================
Presence manager - coordinates all JARVIS UI components.
Single source of truth for overlay, tray, and animations.
"""

import logging
from typing import Optional

from jarvis.runtime.runtime_state import RuntimeStatus, runtime_state
from jarvis.overlay.overlay_manager import overlay_manager
from jarvis.overlay.animation_engine import animation_engine
from jarvis.overlay.status_controller import status_controller

logger = logging.getLogger(__name__)


class PresenceManager:
    def __init__(self):
        self._initialized: bool = False
        logger.info("Presence Manager initialized")

    def initialize(self):
        """Initialize presence manager and all components"""
        if self._initialized:
            logger.warning("Presence manager already initialized")
            return
        logger.info("Initializing presence manager")

        # Register status change callback
        runtime_state.register_status_change_callback(self._on_status_change)

        self._initialized = True

    def start(self):
        """Start all UI components"""
        if not self._initialized:
            self.initialize()
        logger.info("Starting presence manager UI components")
        # Note: overlay is now started in jarvis_runtime.py main thread

    def _on_status_change(self, old_status: RuntimeStatus, new_status: RuntimeStatus):
        """Handle status change events"""
        logger.debug(f"Presence manager status change: {old_status} → {new_status}")
        overlay_manager.update_status_display(new_status)

    def toggle_pause(self):
        """Toggle pause state"""
        status_controller.toggle_pause()

    def set_status(self, status: RuntimeStatus):
        """Set the current status"""
        status_controller.set_status(status)

    def stop(self):
        """Stop all UI components"""
        logger.info("Stopping presence manager")
        overlay_manager.stop()


# Module-level singleton
presence_manager = PresenceManager()

