
"""
Runtime API Module
=================
API for interacting with JARVIS runtime services
"""
import logging
from typing import Dict, Any, Optional

from jarvis.runtime.event_bus import event_bus, Event, EventType
from jarvis.runtime.runtime_state_machine import runtime_state_machine, RuntimeState

logger = logging.getLogger(__name__)


class RuntimeAPI:
    """API for controlling the JARVIS runtime."""

    def __init__(self):
        logger.info("RuntimeAPI initialized")

    def pause(self):
        """Pause the JARVIS runtime."""
        event_bus.publish(Event(EventType.PAUSE, source="api"))
        logger.info("Pause command sent via API")

    def resume(self):
        """Resume the JARVIS runtime."""
        event_bus.publish(Event(EventType.RESUME, source="api"))
        logger.info("Resume command sent via API")

    def get_state(self) -> RuntimeState:
        """Get current runtime state."""
        return runtime_state_machine.current_state

    def execute_task(self, task: str):
        """Execute a task via API."""
        event_bus.publish(Event(EventType.COMMAND_RECEIVED, data=task, source="api"))
        logger.info(f"Task execution requested: {task}")


# Module-level singleton
runtime_api = RuntimeAPI()

