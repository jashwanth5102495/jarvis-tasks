
"""
background_service.py
=====================
Background idle loop for JARVIS persistent runtime system.
Maintains continuous execution with minimal CPU usage while idle.
"""

import logging
import asyncio
from typing import Optional

from runtime.runtime_state import runtime_state, RuntimeStatus

logger = logging.getLogger(__name__)


class BackgroundService:
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._task: Optional[asyncio.Task] = None

    def initialize(self) -> None:
        logger.debug("Background service initialized (no-op)")

    def start(self) -> None:
        logger.info("Starting background service")
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._task = self._loop.create_task(self._idle_loop())
        try:
            self._loop.run_until_complete(self._task)
        except asyncio.CancelledError:
            logger.debug("Background service loop cancelled")
        except Exception as e:
            logger.error(f"Background service error: {e}", exc_info=True)

    async def _idle_loop(self) -> None:
        logger.info("Entering idle loop")
        try:
            while runtime_state.is_running:
                if runtime_state.current_status != RuntimeStatus.SHUTTING_DOWN:
                    # Low-CPU sleep when idle
                    await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(0.05)
        finally:
            logger.info("Idle loop stopped")

    def stop(self) -> None:
        logger.info("Stopping background service")
        if self._task and not self._task.done():
            self._task.cancel()
        if self._loop and self._loop.is_running():
            self._loop.stop()


# Module-level singleton
background_service = BackgroundService()

