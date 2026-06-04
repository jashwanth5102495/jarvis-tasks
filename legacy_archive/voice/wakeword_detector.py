
"""
wakeword_detector.py
==================
Wake-word detection system for JARVIS. Listens for activation phrases
like "Jarvis" or "Hey Jarvis" to initiate conversations.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional, Callable, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WakewordConfig:
    """Configuration for wake-word detection."""
    wakewords: List[str] = field(default_factory=lambda: ["jarvis", "hey jarvis"])
    confidence_threshold: float = 0.7
    cooldown_seconds: float = 2.0
    sample_rate: int = 16000


class WakewordDetector:
    """
    Wake-word detector for JARVIS.
    Listens for activation phrases to start conversations.
    """

    def __init__(self):
        self.config = WakewordConfig()
        self._callback: Optional[Callable[[str], None]] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._last_detection_time: float = 0.0

    def set_wakeword_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback to invoke when a wake-word is detected."""
        self._callback = callback

    def add_wakeword(self, wakeword: str) -> None:
        """Add a new wake-word to listen for."""
        wakeword_lower = wakeword.lower()
        if wakeword_lower not in self.config.wakewords:
            self.config.wakewords.append(wakeword_lower)
            logger.info(f"Added wake-word: {wakeword}")

    def remove_wakeword(self, wakeword: str) -> None:
        """Remove a wake-word from the list."""
        wakeword_lower = wakeword.lower()
        if wakeword_lower in self.config.wakewords:
            self.config.wakewords.remove(wakeword_lower)
            logger.info(f"Removed wake-word: {wakeword}")

    def start(self) -> None:
        """Start the wake-word detector."""
        if self._running:
            logger.warning("Wake-word detector already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._detect_loop, daemon=True)
        self._thread.start()
        logger.info("Wake-word detector started")

    def stop(self) -> None:
        """Stop the wake-word detector."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Wake-word detector stopped")

    def _detect_loop(self) -> None:
        """Main loop for wake-word detection."""
        # This is a mock implementation for testing
        # In production, integrate with Porcupine, Snowboy, or custom detection
        logger.info("Wake-word detection loop running (mock mode)")
        
        while self._running:
            try:
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in wake-word detection: {e}")

    def simulate_detection(self, wakeword: str = "jarvis") -> None:
        """Simulate wake-word detection for testing."""
        current_time = time.time()
        
        if current_time - self._last_detection_time < self.config.cooldown_seconds:
            logger.debug("Wake-word detection in cooldown")
            return
        
        self._last_detection_time = current_time
        
        if self._callback:
            self._callback(wakeword)
            logger.info(f"Simulated wake-word detection: {wakeword}")


# Module-level singleton
wakeword_detector = WakewordDetector()

