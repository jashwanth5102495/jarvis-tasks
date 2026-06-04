
"""
base_engine.py
==============
Abstract base class for all JARVIS TTS engines.
Defines the common interface that all TTS engines must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path


class TTSEngine(ABC):
    """
    Abstract base class for TTS engines.
    All TTS engines must inherit from this and implement the required methods.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.is_initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the TTS engine, load models, etc.
        Returns True if initialization succeeded, False otherwise.
        """
        pass

    @abstractmethod
    def speak(self, text: str) -> bool:
        """
        Speak the given text aloud.
        Returns True if speech was successful, False otherwise.
        """
        pass

    @abstractmethod
    def stop(self):
        """Stop any ongoing speech immediately."""
        pass

    @abstractmethod
    def get_available_voices(self) -> list:
        """Return list of available voice names for this engine."""
        pass

    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """Set the current voice to the given voice ID."""
        pass

    @abstractmethod
    def set_speed(self, speed: float) -> bool:
        """Set speech speed (1.0 is normal, 0.5 is half, 2.0 is double)."""
        pass

    @abstractmethod
    def set_volume(self, volume: float) -> bool:
        """Set speech volume (0.0 to 1.0)."""
        pass

