
"""
runtime_state_machine.py
======================
Finite State Machine for JARVIS Runtime Core.
Manages all runtime states and transitions.
"""

import logging
from enum import Enum, auto
from typing import Optional
from runtime.event_bus import event_bus, EventType, Event

logger = logging.getLogger(__name__)


class RuntimeState(Enum):
    """All possible states for JARVIS Runtime."""
    IDLE = auto()
    LISTENING = auto()
    THINKING = auto()
    EXECUTING = auto()
    SPEAKING = auto()
    PAUSED = auto()
    RECOVERING = auto()
    ERROR = auto()
    SHUTTING_DOWN = auto()


class RuntimeStateMachine:
    """Manages state transitions and current state."""
    _instance = None
    _lock = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuntimeStateMachine, cls).__new__(cls)
            cls._instance._current_state = RuntimeState.IDLE
            cls._instance._previous_state = RuntimeState.IDLE
            logger.info("Runtime State Machine initialized at IDLE")
        return cls._instance

    @property
    def current_state(self) -> RuntimeState:
        return self._current_state

    def transition_to(self, new_state: RuntimeState) -> bool:
        """
        Transition to a new state.
        Returns True if transition is valid or we're already in that state.
        """
        if new_state == self._current_state:
            logger.debug(f"Already in state {new_state.name}")
            return True
        
        valid_transitions = self._get_valid_transitions(self._current_state)
        
        if new_state in valid_transitions:
            self._previous_state = self._current_state
            self._current_state = new_state
            logger.info(f"State transition: {self._previous_state.name} -> {new_state.name}")
            
            # Publish state change event
            event_bus.publish(
                Event(
                    event_type=EventType.STATE_CHANGE,
                    data={
                        "old_state": self._previous_state,
                        "new_state": self._current_state
                    },
                    source="state_machine"
                )
            )
            return True
        
        logger.warning(f"Invalid transition attempt: {self._current_state.name} -> {new_state.name}")
        return False

    def _get_valid_transitions(self, from_state: RuntimeState) -> list:
        """Define valid state transitions."""
        transitions = {
            RuntimeState.IDLE: [
                RuntimeState.LISTENING,
                RuntimeState.EXECUTING,
                RuntimeState.PAUSED,
                RuntimeState.SHUTTING_DOWN
            ],
            RuntimeState.LISTENING: [
                RuntimeState.THINKING,
                RuntimeState.IDLE,
                RuntimeState.PAUSED,
                RuntimeState.ERROR
            ],
            RuntimeState.THINKING: [
                RuntimeState.EXECUTING,
                RuntimeState.SPEAKING,
                RuntimeState.IDLE,
                RuntimeState.ERROR
            ],
            RuntimeState.EXECUTING: [
                RuntimeState.SPEAKING,
                RuntimeState.IDLE,
                RuntimeState.ERROR
            ],
            RuntimeState.SPEAKING: [
                RuntimeState.IDLE,
                RuntimeState.LISTENING,
                RuntimeState.PAUSED
            ],
            RuntimeState.PAUSED: [
                RuntimeState.IDLE,
                RuntimeState.SHUTTING_DOWN
            ],
            RuntimeState.ERROR: [
                RuntimeState.RECOVERING,
                RuntimeState.IDLE,
                RuntimeState.SHUTTING_DOWN
            ],
            RuntimeState.RECOVERING: [
                RuntimeState.IDLE,
                RuntimeState.SHUTTING_DOWN
            ]
        }
        return transitions.get(from_state, [])

    def reset_to_idle(self):
        """Force reset to IDLE state (used for recovery)."""
        self._previous_state = self._current_state
        self._current_state = RuntimeState.IDLE
        logger.info("Force reset to IDLE state")
        event_bus.publish(
            Event(
                event_type=EventType.STATE_CHANGE,
                data={
                    "old_state": self._previous_state,
                    "new_state": self._current_state
                },
                source="state_machine"
            )
        )


# Module-level singleton
runtime_state_machine = RuntimeStateMachine()
