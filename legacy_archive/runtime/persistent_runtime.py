
"""
persistent_runtime.py
===================
Infinite Persistent AI Runtime Loop for JARVIS AI Operating System.
Implements event-driven, asyncio-based continuous runtime.
"""

import logging
import asyncio
from typing import Optional
from runtime.lifecycle_manager import lifecycle_manager
from runtime.event_bus import event_bus, EventType, Event
from runtime.runtime_state_machine import runtime_state_machine, RuntimeState

logger = logging.getLogger(__name__)


class PersistentRuntime:
    """Infinite runtime loop for JARVIS."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PersistentRuntime, cls).__new__(cls)
            cls._instance._loop_task: Optional[asyncio.Task] = None
            cls._instance._is_running = False
            logger.info("Persistent Runtime initialized")
        return cls._instance

    async def run(self) -> None:
        """Start the infinite runtime loop."""
        self._is_running = True

        # Start lifecycle manager first
        await lifecycle_manager.start()

        logger.info("Starting infinite runtime loop...")

        try:
            while self._is_running:
                await self._main_loop_tick()
                await asyncio.sleep(0.1)  # Optimized sleep for minimal CPU usage

        except Exception as e:
            logger.critical(f"Fatal error in runtime loop: {e}", exc_info=True)
            runtime_state_machine.transition_to(RuntimeState.ERROR)

        logger.info("Infinite runtime loop exited")

    async def _main_loop_tick(self) -> None:
        """Single iteration of the runtime loop."""
        # Check runtime state and act accordingly
        current_state = runtime_state_machine.current_state

        if current_state == RuntimeState.IDLE:
            await self._idle_tick()
        elif current_state == RuntimeState.PAUSED:
            await self._paused_tick()
        # Other states are handled by event subscribers
        else:
            pass

    async def _idle_tick(self) -> None:
        """What to do when in IDLE state."""
        # In idle, we just maintain low resource usage
        # The voice listener will trigger events if it detects wake word
        pass

    async def _paused_tick(self) -> None:
        """What to do when in PAUSED state."""
        # All listeners and agents are suspended
        pass

    def stop(self) -> None:
        """Stop the infinite runtime loop."""
        logger.info("Stopping persistent runtime...")
        self._is_running = False


# Module-level singleton
persistent_runtime = PersistentRuntime()
