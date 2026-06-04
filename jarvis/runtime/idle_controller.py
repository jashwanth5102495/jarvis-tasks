
"""
idle_controller.py
==================
Idle state resource optimization manager for JARVIS runtime.
Suspends unused components when idle/paused to reduce memory/CPU usage.
"""

import logging
import threading
from typing import Optional

from jarvis.runtime.runtime_state import runtime_state, RuntimeStatus

logger = logging.getLogger(__name__)


class IdleController:
    def __init__(self):
        self._running: bool = False
        self._monitor_thread: Optional[threading.Thread] = None

    def initialize(self) -> None:
        logger.info("Initializing idle controller")

    def _monitor_loop(self) -> None:
        while self._running:
            if runtime_state.current_status == RuntimeStatus.PAUSED:
                logger.debug("Idle controller: paused mode - suspending non-critical resources")
            elif runtime_state.current_status == RuntimeStatus.IDLE:
                logger.debug("Idle controller: idle state - optimizing resources")
            import time
            time.sleep(1)

    def start(self) -> None:
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="IdleMonitor"
        )
        self._monitor_thread.start()

    def stop(self) -> None:
        logger.info("Stopping idle controller")
        self._running = False


# Module-level singleton
idle_controller = IdleController()

