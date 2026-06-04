
"""
status_controller.py
====================
Status control logic for JARVIS UI.
Manages status transitions and UI updates.
"""

import logging
from typing import Optional

from runtime.runtime_state import RuntimeStatus, runtime_state

logger = logging.getLogger(__name__)


class StatusController:
    def __init__(self):
        self._current_status: RuntimeStatus = RuntimeStatus.IDLE
        logger.info("Status Controller initialized")

    def set_status(self, status: RuntimeStatus):
        """Set the current status"""
        if status == self._current_status:
            return
        old_status = self._current_status
        self._current_status = status
        logger.info(f"Status transition: {old_status.name} → {status.name}")
        runtime_state.set_status(status)

    def get_current_status(self) -> RuntimeStatus:
        """Get current status"""
        return self._current_status

    def toggle_pause(self):
        """Toggle pause/resume"""
        runtime_state.toggle_pause()
        self._current_status = runtime_state.current_status


status_controller = StatusController()

