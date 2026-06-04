
"""
text_to_speech.py
===============
Advanced text-to-speech system for JARVIS.
Uses multiple interchangeable TTS engines (Piper, pyttsx3, etc.) with voice profiles.
"""

from __future__ import annotations

import logging
import threading
import queue
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from .voice_profile_manager import voice_profile_manager
from .tts_engines.engine_selector import engine_selector

logger = logging.getLogger(__name__)


class VoicePersonality(Enum):
    """Available voice personalities."""
    PROFESSIONAL = "professional"
    ASSISTANT = "assistant"
    MINIMAL = "minimal"
    TECHNICAL = "technical"


@dataclass
class TTSConfig:
    """Configuration for text-to-speech."""
    engine: str = "piper"
    voice_personality: VoicePersonality = VoicePersonality.ASSISTANT
    speed: float = 1.0
    volume: float = 1.0
    streaming: bool = True
    language: str = "en"
    voice_id: Optional[str] = None


class TextToSpeech:
    """
    Advanced text-to-speech system for JARVIS.
    Uses multiple interchangeable TTS engines with voice profile management.
    """

    def __init__(self):
        self.config = TTSConfig()
        self._speaking: bool = False
        self._speech_queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._should_stop: bool = False
        self._engine = None
        self._load_profile_and_engine()

    def _load_profile_and_engine(self):
        # Load profile
        profile = voice_profile_manager.get_current_profile()
        logger.info(f"Loading voice profile: {voice_profile_manager.current_profile_name}")
        # Update config
        self.config.engine = profile.get("engine", "piper")
        self.config.speed = profile.get("speed", 1.0)
        self.config.volume = profile.get("volume", 1.0)
        # Initialize engine
        self._engine = engine_selector.get_engine(self.config.engine, profile)
        if self._engine:
            self._engine.set_speed(self.config.speed)
            self._engine.set_volume(self.config.volume)

    def speak(self, text: str) -> bool:
        """Speak the given text aloud."""
        if not text.strip():
            return True
        if not self._engine:
            logger.error("No TTS engine available!")
            return False
        try:
            self._should_stop = False
            self._speaking = True
            logger.info(f"Speaking: {text}")
            success = self._engine.speak(text)
            logger.info(f"TTS finished speaking (success: {success})")
            return success
        except Exception as e:
            logger.error(f"Error while speaking: {e}", exc_info=True)
            return False
        finally:
            self._speaking = False

    def stop(self):
        """Stop any ongoing speech immediately."""
        self._should_stop = True
        if self._engine:
            self._engine.stop()
        self._speaking = False
        logger.info("TTS stopped")

    def is_speaking(self) -> bool:
        """Check if TTS is currently speaking."""
        return self._speaking

    def set_personality(self, personality: VoicePersonality):
        """Set the voice personality."""
        # Map to profile names
        personality_map = {
            VoicePersonality.PROFESSIONAL: "professional",
            VoicePersonality.ASSISTANT: "jarvis_classic",
            VoicePersonality.TECHNICAL: "technical",
            VoicePersonality.MINIMAL: "friendly"
        }
        profile_name = personality_map.get(personality, "jarvis_classic")
        self.set_profile(profile_name)

    def set_profile(self, profile_name: str):
        """Switch to a different voice profile."""
        if voice_profile_manager.set_profile(profile_name):
            self._load_profile_and_engine()

    def set_speed(self, speed: float):
        """Set speech speed (0.5 to 2.0)."""
        self.config.speed = max(0.5, min(2.0, speed))
        if self._engine:
            self._engine.set_speed(self.config.speed)

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.config.volume = max(0.0, min(1.0, volume))
        if self._engine:
            self._engine.set_volume(self.config.volume)

    def set_voice(self, voice_id: str):
        """Set the current voice by ID."""
        if self._engine:
            if self._engine.set_voice(voice_id):
                self.config.voice_id = voice_id

    def list_voices(self) -> list:
        """List all available voices for current engine."""
        if self._engine:
            return self._engine.get_available_voices()
        return []


# Module-level singleton
text_to_speech = TextToSpeech()

