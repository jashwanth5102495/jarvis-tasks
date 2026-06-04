
"""
lifecycle_manager.py
==================
Central AI Operating Lifecycle Controller for JARVIS.
Manages startup, supervision, recovery, and graceful shutdown.
"""

import logging
import asyncio
import signal
import sys
from typing import Optional
from jarvis.runtime.event_bus import event_bus, EventType, Event
from jarvis.runtime.runtime_state_machine import runtime_state_machine, RuntimeState

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manages the complete runtime lifecycle of JARVIS."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LifecycleManager, cls).__new__(cls)
            cls._instance._is_shutting_down = False
            cls._instance._is_paused = False
            logger.info("Lifecycle Manager initialized")
        return cls._instance

    async def start(self) -> None:
        """Start the complete JARVIS runtime system."""
        logger.info("=" * 70)
        logger.info("JARVIS AI Operating System - Boot Sequence Starting")
        logger.info("=" * 70)

        # Register shutdown handlers
        self._setup_signal_handlers()

        # Subscribe to events
        event_bus.subscribe(EventType.PAUSE, self._on_pause)
        event_bus.subscribe(EventType.RESUME, self._on_resume)
        event_bus.subscribe(EventType.SHUTDOWN, self._on_shutdown)

        # Initialize all subsystems (placeholder for now)
        logger.info("Initializing core subsystems...")

        # Transition to IDLE
        runtime_state_machine.transition_to(RuntimeState.IDLE)

        logger.info("=" * 70)
        logger.info("JARVIS AI Operating System - Boot Complete")
        logger.info("=" * 70)

    def _setup_signal_handlers(self) -> None:
        """Setup OS signal handlers for graceful shutdown."""
        if sys.platform == "win32":
            # Windows uses different signals
            logger.debug("Setting up Windows signal handlers")
        else:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        logger.debug("Signal handlers set up")

    def _signal_handler(self, signum, frame) -> None:
        """Handle OS signals for shutdown."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        event_bus.publish(Event(EventType.SHUTDOWN, source="signal_handler"))

    async def _on_pause(self, event: Event) -> None:
        """Handle PAUSE event."""
        if not self._is_paused:
            logger.info("Pausing JARVIS runtime...")
            self._is_paused = True
            runtime_state_machine.transition_to(RuntimeState.PAUSED)

    async def _on_resume(self, event: Event) -> None:
        """Handle RESUME event."""
        if self._is_paused:
            logger.info("Resuming JARVIS runtime...")
            self._is_paused = False
            runtime_state_machine.transition_to(RuntimeState.IDLE)

    async def _on_shutdown(self, event: Event) -> None:
        """Handle SHUTDOWN event."""
        if not self._is_shutting_down:
            self._is_shutting_down = True
            await self.shutdown()

    async def shutdown(self) -> None:
        """Initiate graceful shutdown sequence."""
        logger.info("=" * 70)
        logger.info("JARVIS AI Operating System - Shutdown Sequence Starting")
        logger.info("=" * 70)

        runtime_state_machine.transition_to(RuntimeState.SHUTTING_DOWN)

        # Give time for cleanup
        await asyncio.sleep(0.5)

        logger.info("=" * 70)
        logger.info("JARVIS AI Operating System - Shutdown Complete")
        logger.info("=" * 70)

        sys.exit(0)


# Module-level singleton
lifecycle_manager = LifecycleManager()
