
import pyaudio
import numpy as np
from typing import Optional, Callable
import threading
from .config import Config
from .audio_utils import pcm16_to_float


class MicrophoneManager:
    def __init__(self):
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_callback: Optional[Callable[[np.ndarray], None]] = None

    def start(self, callback: Callable[[np.ndarray], None]):
        """Start the microphone stream with a callback for audio data."""
        if self._running:
            return

        self._audio_callback = callback
        self.pyaudio_instance = pyaudio.PyAudio()
        
        self.stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=Config.CHANNELS,
            rate=Config.SAMPLE_RATE,
            input=True,
            frames_per_buffer=Config.CHUNK_SIZE
        )
        
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the microphone stream."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()

    def _read_loop(self):
        """Internal loop to read audio data from the microphone."""
        while self._running and self.stream:
            try:
                pcm_data = self.stream.read(Config.CHUNK_SIZE, exception_on_overflow=False)
                audio_float = pcm16_to_float(pcm_data)
                if self._audio_callback:
                    self._audio_callback(audio_float)
            except Exception as e:
                print(f"[JARVIS] Microphone error: {e}")
                break
