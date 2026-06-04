
"""
event_bus.py
============
Event-driven communication backbone for JARVIS AI Operating System.
All components communicate through this centralized event system.
"""

import logging
import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum, auto
from threading import Lock

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events that can be published/subscribed to."""
    STATE_CHANGE = auto()
    VOICE_COMMAND = auto()
    WAKE_WORD_DETECTED = auto()
    COMMAND_RECEIVED = auto()
    THINKING_STARTED = auto()
    EXECUTION_STARTED = auto()
    WORKFLOW_START = auto()
    WORKFLOW_COMPLETE = auto()
    PAUSE = auto()
    RESUME = auto()
    SPEAK_START = auto()
    SPEAK_END = auto()
    ERROR = auto()
    SHUTDOWN = auto()


@dataclass
class Event:
    """Represents a single event in the system."""
    event_type: EventType
    data: Any = None
    source: str = "system"


class EventBus:
    """Central event bus for JARVIS runtime communication."""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers: Dict[EventType, List[Callable]] = {}
                cls._instance._history: List[Event] = []
                logger.info("Event Bus initialized")
        return cls._instance

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe a callback to an event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                logger.debug(f"Subscribed to {event_type.name}")

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe a callback from an event type."""
        with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type.name}")

    def publish(self, event: Event):
        """Publish an event to all subscribers."""
        logger.info(f"Publishing event: {event.event_type.name} from {event.source}")
        with self._lock:
            self._history.append(event)
            if len(self._history) > 1000:
                self._history = self._history[-500:]

            if event.event_type in self._subscribers:
                for callback in self._subscribers[event.event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            # Try to get current event loop
                            try:
                                loop = asyncio.get_running_loop()
                            except RuntimeError:
                                loop = None
                            if loop and loop.is_running():
                                loop.create_task(callback(event))
                            else:
                                logger.warning(f"Async callback {callback} ignored (no running loop)")
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Error in event callback: {e}", exc_info=True)

    def get_history(self, limit: int = 100) -> List[Event]:
        """Get recent event history."""
        with self._lock:
            return self._history[-limit:]


# Module-level singleton
event_bus = EventBus()
