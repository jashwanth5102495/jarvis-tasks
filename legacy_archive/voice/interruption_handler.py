
"""
interruption_handler.py
====================
Interruption handling system for JARVIS. Detects and handles
interruption commands like "stop" or "cancel".
"""

from __future__ import annotations

import logging
from typing import Optional, Callable, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InterruptionConfig:
    """Configuration for interruption detection."""
    interruption_phrases: List[str] = field(default_factory=lambda: [
        "stop",
        "cancel",
        "halt",
        "pause",
        "jarvis stop",
        "hey jarvis stop"
    ])
    emergency_stop_phrases: List[str] = field(default_factory=lambda: [
        "emergency stop",
        "stop everything",
        "halt all"
    ])


class InterruptionHandler:
    """
    Handles interruptions for JARVIS.
    Detects stop commands and halts TTS and workflows safely.
    """

    def __init__(self):
        self.config = InterruptionConfig()
        self._interruption_callback: Optional[Callable[[str], None]] = None

    def set_interruption_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback to invoke when an interruption is detected."""
        self._interruption_callback = callback

    def check_interruption(self, text: str) -> bool:
        """Check if text contains an interruption phrase."""
        text_lower = text.lower().strip()
        
        # Check for emergency stop phrases first
        for phrase in self.config.emergency_stop_phrases:
            if phrase in text_lower:
                self._handle_interruption(text, emergency=True)
                return True
        
        # Check for regular interruption phrases
        for phrase in self.config.interruption_phrases:
            if text_lower == phrase or text_lower.startswith(phrase + " "):
                self._handle_interruption(text, emergency=False)
                return True
        
        return False

    def _handle_interruption(self, text: str, emergency: bool) -> None:
        """Handle an interruption."""
        logger.warning(f"Interruption detected: {text} (emergency: {emergency})")
        
        if self._interruption_callback:
            reason = "emergency_stop" if emergency else "user_stop"
            self._interruption_callback(reason)

    def add_interruption_phrase(self, phrase: str) -> None:
        """Add a new interruption phrase."""
        phrase_lower = phrase.lower()
        if phrase_lower not in self.config.interruption_phrases:
            self.config.interruption_phrases.append(phrase_lower)
            logger.info(f"Added interruption phrase: {phrase}")

    def remove_interruption_phrase(self, phrase: str) -> None:
        """Remove an interruption phrase."""
        phrase_lower = phrase.lower()
        if phrase_lower in self.config.interruption_phrases:
            self.config.interruption_phrases.remove(phrase_lower)
            logger.info(f"Removed interruption phrase: {phrase}")


# Module-level singleton
interruption_handler = InterruptionHandler()

