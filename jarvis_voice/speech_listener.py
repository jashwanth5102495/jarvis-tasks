
import numpy as np
import time
from typing import Optional, Callable
from .config import Config
from .audio_utils import calculate_rms


class SpeechListener:
    def __init__(self):
        self._recording = False
        self._audio_buffer: list[np.ndarray] = []
        self._silence_start_time: float = 0.0
        self._record_start_time: float = 0.0
        self._recording_callback: Optional[Callable[[np.ndarray], None]] = None

    def start_recording(self, callback: Callable[[np.ndarray], None]):
        """Start recording audio."""
        self._recording = True
        self._audio_buffer = []
        self._silence_start_time = 0.0
        self._record_start_time = time.time()
        self._recording_callback = callback
        print("[JARVIS] Recording command...")

    def add_audio(self, audio_data: np.ndarray):
        """Add audio data to buffer if recording."""
        if not self._recording:
            return

        self._audio_buffer.append(audio_data)
        
        # Calculate RMS for silence detection
        rms = calculate_rms(audio_data)
        
        if rms < Config.SILENCE_THRESHOLD:
            if self._silence_start_time == 0:
                self._silence_start_time = time.time()
            elif time.time() - self._silence_start_time >= Config.SILENCE_DURATION:
                self._stop_recording()
        else:
            self._silence_start_time = 0.0

        # Check timeout
        if time.time() - self._record_start_time >= Config.RECORDING_TIMEOUT:
            self._stop_recording()

    def _stop_recording(self):
        """Stop recording and process the audio."""
        if not self._recording:
            return

        self._recording = False
        
        if self._audio_buffer:
            full_audio = np.concatenate(self._audio_buffer)
            if self._recording_callback:
                self._recording_callback(full_audio)
        
        self._audio_buffer = []
