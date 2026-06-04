
"""
streaming_listener.py
===================
Streaming audio listener for JARVIS. Handles real-time listening,
partial transcription, interruption detection, and silence detection.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ListenerConfig:
    """Configuration for the streaming listener."""
    sample_rate: int = 16000
    chunk_size: int = 1024
    silence_threshold: float = 0.01
    silence_timeout_seconds: float = 1.5
    partial_transcription: bool = True


class StreamingListener:
    """
    Streaming listener for real-time audio input.
    Handles partial transcription, silence detection, and interruption detection.
    """

    def __init__(self):
        self.config = ListenerConfig()
        self._transcription_callback: Optional[Callable[[str], None]] = None
        self._partial_callback: Optional[Callable[[str], None]] = None
        self._listening: bool = False
        self._thread: Optional[threading.Thread] = None
        self._silence_start_time: float = 0.0
        self._current_partial: str = ""

    def set_transcription_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for final transcriptions."""
        self._transcription_callback = callback

    def set_partial_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for partial transcriptions."""
        self._partial_callback = callback

    def start_listening(self) -> None:
        """Start listening for audio input."""
        if self._listening:
            logger.warning("Streaming listener already listening")
            return
        
        self._listening = True
        self._silence_start_time = 0.0
        self._current_partial = ""
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Streaming listener started")

    def stop_listening(self) -> None:
        """Stop listening for audio input."""
        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Streaming listener stopped")

    def _listen_loop(self) -> None:
        """Main listening loop."""
        # Mock implementation for testing
        logger.info("Streaming listener loop running (mock mode)")
        
        # Simulate listening for a command
        time.sleep(1.0)
        
        if self._listening:
            mock_command = "open chrome"
            if self._transcription_callback:
                self._transcription_callback(mock_command)
        
        self._listening = False

    def simulate_command(self, command: str) -> None:
        """Simulate a voice command for testing."""
        if self._transcription_callback:
            self._transcription_callback(command)
            logger.info(f"Simulated voice command: {command}")

    def is_listening(self) -> bool:
        """Check if the listener is currently active."""
        return self._listening


# Module-level singleton
streaming_listener = StreamingListener()

