
"""
runtime_state.py
================
Central runtime state management for JARVIS persistent background system.
Tracks active/paused/listening/speaking states and handles state transitions.
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RuntimeStatus(Enum):
    IDLE = auto()
    LISTENING = auto()
    SPEAKING = auto()
    EXECUTING = auto()
    PAUSED = auto()
    THINKING = auto()
    RECOVERING = auto()
    ERROR = auto()
    SHUTTING_DOWN = auto()


@dataclass
class RuntimeState:
    current_status: RuntimeStatus = RuntimeStatus.IDLE
    last_status_change: datetime = field(default_factory=datetime.now)
    is_running: bool = True
    startup_time: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None

    # Callbacks for state changes
    _status_change_callbacks: List[Callable[[RuntimeStatus, RuntimeStatus], None]] = field(
        default_factory=list,
        repr=False
    )

    def register_status_change_callback(
        self,
        callback: Callable[[RuntimeStatus, RuntimeStatus], None]
    ) -> None:
        self._status_change_callbacks.append(callback)

    def set_status(self, new_status: RuntimeStatus) -> None:
        if new_status == self.current_status:
            return
        old_status = self.current_status
        logger.info(f"Runtime status changing: {old_status.name} → {new_status.name}")
        self.current_status = new_status
        self.last_status_change = datetime.now()
        for callback in self._status_change_callbacks:
            try:
                callback(old_status, new_status)
            except Exception as e:
                logger.error(f"Status change callback failed: {e}", exc_info=True)

    def toggle_pause(self) -> bool:
        if self.current_status == RuntimeStatus.PAUSED:
            self.set_status(RuntimeStatus.IDLE)
            return True
        elif self.current_status != RuntimeStatus.SHUTTING_DOWN:
            self.set_status(RuntimeStatus.PAUSED)
            return True
        return False


# Module-level singleton instance
runtime_state = RuntimeState()

