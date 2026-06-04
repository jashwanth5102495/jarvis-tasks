
"""
pyttsx3_engine.py
==================
Fallback TTS engine using pyttsx3 (Windows SAPI5).
Used when Piper isn't available.
"""

import logging
from typing import Optional

from .base_engine import TTSEngine

logger = logging.getLogger(__name__)


class Pyttsx3TTSEngine(TTSEngine):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.voice_id = self.config.get("voice", None)
        self.speed = self.config.get("speed", 150)  # Normal speed (default ~150)
        self.volume = self.config.get("volume", 1.0)
        self._engine = None

    def initialize(self) -> bool:
        try:
            import pyttsx3
            logger.info("Initializing pyttsx3 TTS engine...")
            self._engine = pyttsx3.init(driverName='sapi5')

            # Set volume
            self._engine.setProperty('volume', self.volume)

            # Set initial speed using our scale conversion
            initial_wpm = 150  # Normal speed
            self._engine.setProperty('rate', initial_wpm)
            logger.info(f"Set initial TTS speed to {initial_wpm} WPM")

            # List voices and try to find Microsoft David Desktop
            voices = self._engine.getProperty('voices')
            logger.info(f"Available voices: {len(voices)} found")
            
            # Target voice for Windows desktop
            target_voice = "Microsoft David Desktop"
            selected_voice_id = None
            for i, v in enumerate(voices):
                logger.info(f"  Voice {i}: {v.name}")
                if target_voice in v.name:
                    selected_voice_id = v.id
                    logger.info(f"Found target voice: {v.name}")
                    break
            
            if selected_voice_id:
                self._engine.setProperty('voice', selected_voice_id)
            else:
                logger.warning(f"Could not find voice {target_voice}, using default")
                if voices:
                    self._engine.setProperty('voice', voices[0].id)

            self.is_initialized = True
            logger.info("pyttsx3 TTS initialized successfully!")
            return True
        except ImportError:
            logger.error("pyttsx3 not installed!")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}", exc_info=True)
            return False

    def speak(self, text: str) -> bool:
        if not self.is_initialized or not self._engine:
            logger.error("pyttsx3 not initialized!")
            return False
        try:
            self._engine.say(text)
            self._engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"pyttsx3 failed to speak: {e}", exc_info=True)
            return False

    def stop(self):
        try:
            if self._engine:
                self._engine.stop()
        except Exception as e:
            logger.error(f"Error stopping pyttsx3: {e}")

    def get_available_voices(self) -> list:
        voices = []
        if self._engine:
            pyttsx3_voices = self._engine.getProperty('voices')
            for i, v in enumerate(pyttsx3_voices):
                voices.append(f"{i}: {v.name}")
        return voices

    def set_voice(self, voice_id: str) -> bool:
        if self._engine:
            try:
                self._engine.setProperty('voice', voice_id)
                self.voice_id = voice_id
                return True
            except Exception as e:
                logger.error(f"Failed to set pyttsx3 voice: {e}")
                return False
        return False

    def set_speed(self, speed: float) -> bool:
        if self._engine:
            # Convert 0.5-2.0 scale to reasonable WPM
            # 0.5 = 100 WPM (slow), 1.0 = 150 WPM (normal), 2.0 = 200 WPM (fast)
            base_wpm = 150
            wpm = int(base_wpm + (speed - 1.0) * 100)
            wpm = max(100, min(200, wpm))  # Clamp between 100-200 WPM
            self._engine.setProperty('rate', wpm)
            logger.info(f"Set TTS speed to {wpm} WPM (scale: {speed})")
            self.speed = speed
            return True
        return False

    def set_volume(self, volume: float) -> bool:
        if self._engine:
            self._engine.setProperty('volume', max(0.0, min(1.0, volume)))
            self.volume = volume
            return True
        return False

