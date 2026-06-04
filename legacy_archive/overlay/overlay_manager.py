
"""
overlay_manager.py
=================
PyQt6-based overlay manager for JARVIS cinematic presence.
Manages the AI indicator overlay lifecycle and syncs with runtime_core.
"""

import logging
import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QMetaObject, Qt

from runtime.runtime_state_machine import runtime_state_machine, RuntimeState
from runtime.event_bus import event_bus, EventType, Event
from overlay.ai_indicator import AIIndicator
from overlay.animation_engine import animation_engine

logger = logging.getLogger(__name__)


class OverlayManager:
    def __init__(self):
        self._indicator: Optional[AIIndicator] = None
        self._initialized: bool = False
        self._watchdog_timer: Optional[QTimer] = None
        self._last_command = ""
        logger.info("Overlay Manager initialized")

    def initialize(self):
        """Initialize the overlay manager"""
        if self._initialized:
            logger.warning("Overlay manager already initialized")
            return
        logger.info("Initializing overlay manager")
        
        # Subscribe to ALL events!
        event_bus.subscribe(EventType.STATE_CHANGE, self._on_state_change_event)
        event_bus.subscribe(EventType.PAUSE, self._on_pause_event)
        event_bus.subscribe(EventType.RESUME, self._on_resume_event)
        event_bus.subscribe(EventType.WAKE_WORD_DETECTED, self._on_wake_detected)
        event_bus.subscribe(EventType.COMMAND_RECEIVED, self._on_command_received)
        event_bus.subscribe(EventType.THINKING_STARTED, self._on_thinking_started)
        event_bus.subscribe(EventType.EXECUTION_STARTED, self._on_execution_started)
        event_bus.subscribe(EventType.SPEAK_START, self._on_speak_start)
        event_bus.subscribe(EventType.SPEAK_END, self._on_speak_end)
        
        self._initialized = True

    def start(self):
        """Start the overlay (deprecated, kept for compatibility)"""
        logger.warning("start() is deprecated, use start_in_main_thread() instead")

    def start_in_main_thread(self):
        """Start the overlay in the main thread (must be called after QApplication is created)"""
        if not self._initialized:
            self.initialize()
        if self._indicator:
            logger.warning("Overlay already running")
            return

        logger.info("Creating AIIndicator instance")
        # Create the indicator
        self._indicator = AIIndicator()
        logger.info("AIIndicator created")
        animation_engine.set_target_widget(self._indicator)

        # Set initial status from runtime_core
        self._update_overlay_status(runtime_state_machine.current_state)

        # Fade in
        self._indicator.fade_in(500)

        # Start watchdog to ensure overlay stays visible and in position
        self._start_watchdog()

        logger.info("Overlay started completely")

    def _start_watchdog(self):
        """Start the overlay watchdog to ensure it stays visible"""
        self._watchdog_timer = QTimer()
        self._watchdog_timer.timeout.connect(self.ensure_visible)
        self._watchdog_timer.start(3000)
        logger.info("Overlay watchdog started")

    def ensure_visible(self):
        """Ensure the overlay stays visible and in top-right"""
        if self._indicator:
            self._indicator.ensure_visible()

    def _position_indicator(self):
        """Position the indicator on screen"""
        if not self._indicator:
            return

        # Get screen dimensions
        screen = QApplication.primaryScreen()
        if not screen:
            return
            
        geometry = screen.availableGeometry()

        # Calculate position: 30px from right edge, 30px from top edge
        x = geometry.width() - self._indicator.width() - 30
        y = 30

        # Move the indicator
        self._indicator.move(x, y)
        logger.debug(f"Overlay positioned at ({x}, {y}), size: {self._indicator.size()}")

    def _on_state_change_event(self, event: Event):
        """Handle state change events from event bus"""
        if event.data and "new_state" in event.data:
            new_state = event.data["new_state"]
            details = None
            if new_state == RuntimeState.LISTENING and self._last_command:
                details = f"Heard: \"{self._last_command}\""
            # Use QTimer to update in main thread
            def do_update():
                self._update_overlay_status(new_state, details)
                self._position_indicator()
            app = QApplication.instance()
            if app:
                QTimer.singleShot(0, do_update)

    def _on_pause_event(self, event: Event):
        """Handle pause event"""
        runtime_state_machine.transition_to(RuntimeState.PAUSED)

    def _on_resume_event(self, event: Event):
        """Handle resume event"""
        runtime_state_machine.transition_to(RuntimeState.IDLE)
        
    def _on_wake_detected(self, event: Event):
        """Handle wake word detected event"""
        def do_update():
            self._update_overlay_status(RuntimeState.LISTENING)
        app = QApplication.instance()
        if app:
            QTimer.singleShot(0, do_update)
            
    def _on_command_received(self, event: Event):
        """Handle command received event"""
        self._last_command = event.data
        def do_update():
            self._update_overlay_status(RuntimeState.THINKING, f"Heard: \"{self._last_command}\"")
        app = QApplication.instance()
        if app:
            QTimer.singleShot(0, do_update)
            
    def _on_thinking_started(self, event: Event):
        """Handle thinking started event"""
        def do_update():
            self._update_overlay_status(RuntimeState.THINKING, "Planning workflow...")
        app = QApplication.instance()
        if app:
            QTimer.singleShot(0, do_update)
            
    def _on_execution_started(self, event: Event):
        """Handle execution started event"""
        def do_update():
            self._update_overlay_status(RuntimeState.EXECUTING, f"Executing: \"{event.data}\"")
        app = QApplication.instance()
        if app:
            QTimer.singleShot(0, do_update)
            
    def _on_speak_start(self, event: Event):
        """Handle speak start event"""
        def do_update():
            self._update_overlay_status(RuntimeState.SPEAKING, f"\"{event.data}\"")
        app = QApplication.instance()
        if app:
            QTimer.singleShot(0, do_update)
            
    def _on_speak_end(self, event: Event):
        """Handle speak end event"""
        def do_update():
            self._update_overlay_status(RuntimeState.IDLE)
        app = QApplication.instance()
        if app:
            QTimer.singleShot(0, do_update)

    def update_status_display(self, runtime_status):
        """Update overlay UI based on runtime state"""
        if not self._indicator:
            logger.warning("AI indicator not initialized")
            return
        
        # Convert runtime_status to RuntimeState if needed
        if hasattr(runtime_status, 'name'):
            # Check if it's the old RuntimeStatus from runtime module
            state_name = runtime_status.name
        else:
            state_name = str(runtime_status)
        
        # Map to Core RuntimeState
        state_mapping = {
            "IDLE": RuntimeState.IDLE,
            "PAUSED": RuntimeState.PAUSED,
            "LISTENING": RuntimeState.LISTENING,
            "SPEAKING": RuntimeState.SPEAKING,
            "THINKING": RuntimeState.THINKING,
            "EXECUTING": RuntimeState.EXECUTING,
            "RECOVERING": RuntimeState.RECOVERING,
        }
        
        core_state = state_mapping.get(state_name, RuntimeState.IDLE)
        self._update_overlay_status(core_state)

    def _update_overlay_status(self, core_state: RuntimeState, details=None):
        """Update overlay based on Core RuntimeState"""
        self._indicator.set_status(core_state, details)
        logger.info(f"Overlay updated to {core_state.name}" + (f" with details: {details}" if details else ""))

    def stop(self):
        """Stop the overlay"""
        logger.info("Stopping overlay")
        if self._watchdog_timer:
            self._watchdog_timer.stop()
        if self._indicator:
            self._indicator.close()
            self._indicator = None


# Module-level singleton
overlay_manager = OverlayManager()

