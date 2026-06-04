
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
from .config import Config


class SpeechTranscriber:
    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self._initialized = False

    def initialize(self):
        """Initialize Faster Whisper model."""
        if self._initialized:
            return

        try:
            print(f"[JARVIS] Loading Whisper model: {Config.WHISPER_MODEL_SIZE}...")
            self.model = WhisperModel(
                Config.WHISPER_MODEL_SIZE,
                device=Config.WHISPER_DEVICE,
                compute_type="int8" if Config.WHISPER_DEVICE == "cpu" else "float16",
                download_root=str(Config.MODELS_DIR)
            )
            self._initialized = True
            print(f"[JARVIS] Whisper model loaded successfully")
        except Exception as e:
            print(f"[JARVIS] Error loading Whisper model: {e}")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = Config.SAMPLE_RATE) -> str:
        """Transcribe audio data to text."""
        if not self.model or not self._initialized:
            return ""

        try:
            print("[JARVIS] Transcribing...")
            segments, _ = self.model.transcribe(
                audio_data,
                language=Config.WHISPER_LANGUAGE,
                beam_size=5
            )
            
            transcript = " ".join([segment.text.strip() for segment in segments])
            print(f"[JARVIS] Transcript: {transcript}")
            return transcript
        except Exception as e:
            print(f"[JARVIS] Transcription error: {e}")
            return ""
