
"""
speech_to_text.py
===============
Speech-to-text system for JARVIS using Whisper (local, offline).
Supports live microphone listening and streaming transcription.
"""

from __future__ import annotations

import logging
import threading
import queue
from typing import Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class STTConfig:
    """Configuration for speech-to-text."""
    model_name: str = "base"  # tiny, base, small, medium, large
    language: str = "en"
    sample_rate: int = 16000
    chunk_size: int = 1024
    streaming: bool = True


class SpeechToText:
    """
    Speech-to-text system for JARVIS.
    Converts audio from microphone to text using Whisper (local).
    """

    def __init__(self):
        self.config = STTConfig()
        self._transcription_callback: Optional[Callable[[str], None]] = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

    def set_transcription_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback to receive transcriptions."""
        self._transcription_callback = callback

    def start_listening(self) -> None:
        """Start listening to the microphone."""
        if self._running:
            logger.warning("STT already listening")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("STT listening started")

    def stop_listening(self) -> None:
        """Stop listening to the microphone."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("STT listening stopped")

    def _listen_loop(self) -> None:
        """Main listening loop."""
        # Mock implementation for testing
        logger.info("STT listening loop running (mock mode)")

    def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio data to text."""
        # Mock implementation
        mock_transcript = "Hello, this is a mock transcription"
        return mock_transcript

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an audio file to text."""
        # Mock implementation
        logger.info(f"Transcribing file: {file_path}")
        return "Mock transcription from file"


# Module-level singleton
speech_to_text = SpeechToText()

