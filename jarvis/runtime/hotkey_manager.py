
"""
hotkey_manager.py
=================
Global hotkey system for JARVIS. Implements CTRL+P toggle pause/resume.
Uses keyboard library (safe, cross-platform) for global key detection.
Now uses event bus for state management.
"""

import logging
import threading
import time
from typing import Optional
from jarvis.runtime.event_bus import event_bus, EventType, Event
from jarvis.runtime.runtime_state_machine import runtime_state_machine, RuntimeState

logger = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self):
        self._running: bool = False
        self._listener_thread: Optional[threading.Thread] = None
        self._keyboard_lib: Optional[object] = None
        self._last_toggle_time: float = 0.0
        self._debounce_delay: float = 0.3

    def initialize(self) -> None:
        logger.info("Initializing hotkey manager")
        try:
            import keyboard
            self._keyboard_lib = keyboard
            logger.debug("Keyboard library imported successfully")
        except ImportError:
            logger.warning("Keyboard library not found; hotkey system disabled")
            self._keyboard_lib = None
        self._running = True

    def _hotkey_callback(self) -> None:
        import time
        now = time.time()
        if now - self._last_toggle_time < self._debounce_delay:
            logger.debug("Ignoring duplicate hotkey press (debounced)")
            return
        self._last_toggle_time = now
        logger.info("Hotkey CTRL+P pressed: toggling pause/resume")
        
        # Use event bus for pause/resume
        if runtime_state_machine.current_state != RuntimeState.PAUSED:
            event_bus.publish(Event(EventType.PAUSE, source="hotkey"))
        else:
            event_bus.publish(Event(EventType.RESUME, source="hotkey"))

    def start(self) -> None:
        if not self._keyboard_lib:
            return
        if self._listener_thread and self._listener_thread.is_alive():
            return
        self._listener_thread = threading.Thread(
            target=self._listen_hotkeys,
            daemon=True,
            name="HotkeyListener"
        )
        self._listener_thread.start()

    def _listen_hotkeys(self) -> None:
        try:
            import keyboard
            keyboard.add_hotkey('ctrl+p', self._hotkey_callback, suppress=False)
            logger.info("Hotkey listener started (CTRL+P registered)")
            keyboard.wait()
        except Exception as e:
            logger.error(f"Hotkey listener error: {e}", exc_info=True)

    def stop(self) -> None:
        logger.info("Stopping hotkey manager")
        self._running = False
        if self._keyboard_lib:
            try:
                self._keyboard_lib.unhook_all_hotkeys()
            except Exception as e:
                logger.warning(f"Error unhooking hotkeys: {e}")


# Module-level singleton
hotkey_manager = HotkeyManager()
