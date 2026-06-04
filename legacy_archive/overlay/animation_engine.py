
"""
animation_engine.py
===================
Cinematic animation engine for JARVIS overlay.
Provides smooth fade, glow, pulse, and breathing animations using PyQt6.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AnimationEngine:
    def __init__(self):
        logger.info("Animation engine initialized")
        self._target_widget: Optional[object] = None
        self._animations: dict = {}

    def set_target_widget(self, widget):
        self._target_widget = widget
        logger.debug(f"Animation target widget set: {widget}")

    def start_pulse_animation(self, color: str, speed: int = 1000):
        """Start pulsing glow animation"""
        logger.debug(f"Starting pulse animation with color: {color}")
        if not self._target_widget:
            return

        if hasattr(self._target_widget, 'start_pulse'):
            self._target_widget.start_pulse(color, speed)

    def start_breathing_animation(self, color: str, speed: int = 2000):
        """Start subtle breathing animation"""
        logger.debug(f"Starting breathing animation with color: {color}")
        if not self._target_widget:
            return

        if hasattr(self._target_widget, 'start_breathing'):
            self._target_widget.start_breathing(color, speed)

    def stop_all_animations(self):
        """Stop all active animations"""
        logger.debug("Stopping all animations")
        if not self._target_widget:
            return

        if hasattr(self._target_widget, 'stop_animations'):
            self._target_widget.stop_animations()

    def fade_in(self, duration: int = 300):
        """Fade in the overlay"""
        logger.debug("Fading in overlay")
        if not self._target_widget:
            return

        if hasattr(self._target_widget, 'fade_in'):
            self._target_widget.fade_in(duration)

    def fade_out(self, duration: int = 300):
        """Fade out the overlay"""
        logger.debug("Fading out overlay")
        if not self._target_widget:
            return

        if hasattr(self._target_widget, 'fade_out'):
            self._target_widget.fade_out(duration)


animation_engine = AnimationEngine()

