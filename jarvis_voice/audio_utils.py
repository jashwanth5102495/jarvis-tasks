
import numpy as np
import wave
from .config import Config


def float_to_pcm16(audio_float: np.ndarray) -> bytes:
    """Convert float32 audio data to PCM16 bytes."""
    audio_int16 = (audio_float * 32767.0).astype(np.int16)
    return audio_int16.tobytes()


def pcm16_to_float(audio_pcm: bytes) -> np.ndarray:
    """Convert PCM16 bytes to float32 numpy array."""
    audio_int16 = np.frombuffer(audio_pcm, dtype=np.int16)
    return audio_int16.astype(np.float32) / 32767.0


def save_wav(file_path: str, audio_data: np.ndarray, sample_rate: int = Config.SAMPLE_RATE):
    """Save audio data to WAV file."""
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(Config.CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(float_to_pcm16(audio_data))


def calculate_rms(audio_data: np.ndarray) -> float:
    """Calculate RMS (Root Mean Square) of audio data."""
    return np.sqrt(np.mean(np.square(audio_data))) if len(audio_data) > 0 else 0.0
