
"""
runtime module
==============
JARVIS persistent background runtime system.
"""

from jarvis.runtime.runtime_state import runtime_state, RuntimeStatus
# from jarvis.runtime.runtime_manager import runtime_manager  # Lazy import to avoid circular import
from jarvis.runtime.background_service import background_service
from jarvis.runtime.hotkey_manager import hotkey_manager
# from jarvis.runtime.tray_manager import tray_manager  # Now using jarvis.overlay version
# from jarvis.runtime.overlay_manager import overlay_manager  # Now using jarvis.overlay version
from jarvis.runtime.wake_listener import wake_listener
from jarvis.runtime.idle_controller import idle_controller
from jarvis.runtime.startup_manager import startup_manager

__all__ = [
    "runtime_state",
    "RuntimeStatus",
    # "runtime_manager",  # Lazy import to avoid circular import
    "background_service",
    "hotkey_manager",
    # "tray_manager",  # Now using runtime_ui version
    # "overlay_manager",  # Now using runtime_ui version
    "wake_listener",
    "idle_controller",
    "startup_manager"
]

