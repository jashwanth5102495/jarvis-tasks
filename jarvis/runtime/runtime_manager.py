
"""
runtime_manager.py
==================
Core runtime orchestration manager for JARVIS persistent background system.
Coordinates all runtime components (hotkeys, tray, overlay, listeners, etc.).
Now integrates with runtime_core event bus.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from jarvis.runtime.runtime_state import runtime_state, RuntimeStatus
from jarvis.runtime.background_service import background_service
from jarvis.runtime.hotkey_manager import hotkey_manager
from jarvis.runtime.wake_listener import wake_listener
from jarvis.runtime.idle_controller import idle_controller
from jarvis.runtime.startup_manager import startup_manager
from jarvis.runtime.event_bus import event_bus, EventType, Event
from jarvis.runtime.runtime_state_machine import runtime_state_machine, RuntimeState as CoreRuntimeState

logger = logging.getLogger(__name__)


class RuntimeManager:
    def __init__(self):
        self._components_initialized: bool = False

    def initialize(self, enable_startup: bool = False) -> None:
        if self._components_initialized:
            logger.warning("Runtime manager already initialized")
            return
        logger.info("Initializing JARVIS runtime system")

        # Subscribe to event bus
        event_bus.subscribe(EventType.PAUSE, self._on_pause_event)
        event_bus.subscribe(EventType.RESUME, self._on_resume_event)

        # Note: UI components (tray, overlay, presence) are now initialized in jarvis_runtime.py main thread

        # Initialize non-UI components
        hotkey_manager.initialize()
        idle_controller.initialize()
        wake_listener.initialize()
        if enable_startup:
            startup_manager.enable_startup()

        # Register status change callbacks to update UI components
        runtime_state.register_status_change_callback(self._on_status_change)
        logger.info("Runtime manager initialized successfully")
        self._components_initialized = True

    def _on_pause_event(self, event: Event) -> None:
        """Handle PAUSE event from event bus"""
        logger.info("Processing pause event from event bus")
        runtime_state.toggle_pause()

    def _on_resume_event(self, event: Event) -> None:
        """Handle RESUME event from event bus"""
        logger.info("Processing resume event from event bus")
        runtime_state.toggle_pause()

    def start(self) -> None:
        logger.info("Starting JARVIS runtime service")
        runtime_state.is_running = True
        # Note: UI components are already started in jarvis_runtime.py
        background_service.start()

    def stop(self) -> None:
        logger.info("Stopping JARVIS runtime service")
        runtime_state.is_running = False
        runtime_state.set_status(RuntimeStatus.SHUTTING_DOWN)
        background_service.stop()
        hotkey_manager.stop()
        # Note: tray and overlay are stopped in jarvis_runtime.py
        wake_listener.stop()
        idle_controller.stop()
        logger.info("Runtime service stopped successfully")

    def _on_status_change(self, old_status: RuntimeStatus, new_status: RuntimeStatus) -> None:
        """Synchronize legacy runtime state with core runtime state"""
        logger.debug(f"Status change callback triggered: {old_status} → {new_status}")
        
        # Map legacy RuntimeStatus to CoreRuntimeState and transition
        status_map = {
            RuntimeStatus.IDLE: CoreRuntimeState.IDLE,
            RuntimeStatus.LISTENING: CoreRuntimeState.LISTENING,
            RuntimeStatus.SPEAKING: CoreRuntimeState.SPEAKING,
            RuntimeStatus.EXECUTING: CoreRuntimeState.EXECUTING,
            RuntimeStatus.PAUSED: CoreRuntimeState.PAUSED,
        }
        
        core_state = status_map.get(new_status)
        if core_state:
            runtime_state_machine.transition_to(core_state)
        
        try:
            # Lazy import to avoid circular import
            from jarvis.overlay.overlay_manager import overlay_manager
            from jarvis.overlay.tray_manager import tray_manager
            overlay_manager.update_status_display(new_status)
            tray_manager.update_tray_icon(new_status)
        except Exception as e:
            logger.error(f"Error updating UI components: {e}", exc_info=True)

    def toggle_pause(self) -> None:
        runtime_state.toggle_pause()

    def shutdown(self) -> None:
        self.stop()
        logger.info("Shutting down JARVIS")
        sys.exit(0)


# Module-level singleton
runtime_manager = RuntimeManager()
