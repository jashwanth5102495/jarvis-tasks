
import pvporcupine
import numpy as np
from typing import Optional, Callable
from .config import Config


class WakeWordEngine:
    def __init__(self):
        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self._wakeword_callback: Optional[Callable[[], None]] = None
        self._initialized = False

    def initialize(self):
        """Initialize Porcupine wake word engine."""
        if self._initialized:
            return

        try:
            if Config.PORCUPINE_ACCESS_KEY:
                self.porcupine = pvporcupine.create(
                    access_key=Config.PORCUPINE_ACCESS_KEY,
                    keywords=[Config.WAKE_WORD]
                )
            else:
                # Fallback: use built-in keyword if no access key
                self.porcupine = pvporcupine.create(
                    keywords=["jarvis"]
                )
            self._initialized = True
            print(f"[JARVIS] Wake word engine initialized for: {Config.WAKE_WORD}")
        except Exception as e:
            print(f"[JARVIS] Error initializing wake word engine: {e}")
            print("[JARVIS] Note: Get a free Porcupine access key from https://console.picovoice.ai/")

    def set_callback(self, callback: Callable[[], None]):
        """Set callback for wake word detection."""
        self._wakeword_callback = callback

    def process(self, audio_data: np.ndarray):
        """Process audio data and check for wake word."""
        if not self.porcupine or not self._initialized:
            return

        # Convert to int16 for Porcupine
        audio_int16 = (audio_data * 32767.0).astype(np.int16)
        
        # Porcupine expects specific frame length
        if len(audio_int16) >= self.porcupine.frame_length:
            for i in range(0, len(audio_int16), self.porcupine.frame_length):
                frame = audio_int16[i:i + self.porcupine.frame_length]
                if len(frame) == self.porcupine.frame_length:
                    keyword_index = self.porcupine.process(frame)
                    if keyword_index >= 0:
                        print(f"[JARVIS] Wake word detected!")
                        if self._wakeword_callback:
                            self._wakeword_callback()

    def cleanup(self):
        """Clean up resources."""
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        self._initialized = False
