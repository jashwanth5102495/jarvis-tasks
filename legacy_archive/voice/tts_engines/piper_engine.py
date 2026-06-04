
"""
piper_engine.py
===============
Piper TTS engine for JARVIS.
Lightweight, fast, offline neural TTS with excellent natural voices.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .base_engine import TTSEngine

logger = logging.getLogger(__name__)


class PiperTTSEngine(TTSEngine):
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.voice_id = self.config.get("voice", "en_US-lessac-medium")
        self.speed = self.config.get("speed", 1.0)
        self.volume = self.config.get("volume", 1.0)
        self._piper = None
        self._audio_player = None

    def initialize(self) -> bool:
        try:
            logger.info("Initializing Piper TTS engine...")
            from piper import PiperVoice
            from piper.download import ensure_voice_exists
            import sounddevice as sd
            import numpy as np

            # Get voice and model directories
            voice_dir = Path(__file__).parent.parent.parent / "models" / "piper"
            voice_dir.mkdir(parents=True, exist_ok=True)

            # Ensure voice model exists, download if not
            ensure_voice_exists(
                self.voice_id,
                str(voice_dir),
                str(voice_dir)
            )

            # Load voice
            model_path = voice_dir / f"{self.voice_id}.onnx"
            config_path = voice_dir / f"{self.voice_id}.onnx.json"
            self._piper = PiperVoice.load(str(model_path), config_path=str(config_path))
            logger.info(f"Piper voice loaded: {self.voice_id}")

            # Store audio player
            self._audio_player = sd
            self._np = np

            self.is_initialized = True
            logger.info("Piper TTS initialized successfully!")
            return True

        except ImportError as e:
            logger.error(f"Piper TTS dependencies not installed: {e}")
            logger.warning("To install Piper: pip install piper-tts sounddevice numpy")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}", exc_info=True)
            return False

    def speak(self, text: str) -> bool:
        if not self.is_initialized or not self._piper:
            logger.error("Piper TTS not initialized!")
            return False
        try:
            # Generate audio
            audio = b""
            for audio_bytes in self._piper.synthesize_stream_raw(text):
                audio += audio_bytes

            # Convert to numpy array (int16, 22050 Hz, mono)
            sample_width = 2
            num_samples = len(audio) // sample_width
            audio_array = self._np.frombuffer(audio, dtype=self._np.int16)

            # Play using sounddevice
            self._audio_player.play(
                audio_array,
                samplerate=self._piper.config.sample_rate,
                blocking=True
            )
            self._audio_player.wait()
            return True
        except Exception as e:
            logger.error(f"Piper TTS failed to speak: {e}", exc_info=True)
            return False

    def stop(self):
        try:
            if self._audio_player:
                self._audio_player.stop()
        except Exception as e:
            logger.error(f"Error stopping Piper audio: {e}")

    def get_available_voices(self) -> list:
        # Return common Piper voices
        return [
            "en_US-lessac-medium",
            "en_US-ryan-high",
            "en_GB-alan-medium",
            "en_US-amy-medium",
            "en_US-kathleen-low",
            "en_US-danny-low"
        ]

    def set_voice(self, voice_id: str) -> bool:
        if voice_id in self.get_available_voices():
            self.voice_id = voice_id
            self.is_initialized = False
            return self.initialize()
        else:
            logger.warning(f"Unknown Piper voice: {voice_id}")
            return False

    def set_speed(self, speed: float) -> bool:
        self.speed = max(0.5, min(2.0, speed))
        logger.info(f"Piper speed set to: {self.speed}")
        return True

    def set_volume(self, volume: float) -> bool:
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Piper volume set to: {self.volume}")
        return True

