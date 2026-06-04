
import os
from pathlib import Path


class Config:
    # Paths
    BASE_DIR = Path(__file__).parent
    MODELS_DIR = BASE_DIR / "models"
    
    # Microphone
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 512
    CHANNELS = 1
    
    # Wake Word
    WAKE_WORD = "jarvis"
    PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")
    
    # Speech Recognition
    WHISPER_MODEL_SIZE = "base"
    WHISPER_LANGUAGE = "en"
    WHISPER_DEVICE = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu"
    
    # Command Recording
    RECORDING_TIMEOUT = 5  # seconds
    SILENCE_THRESHOLD = 0.01
    SILENCE_DURATION = 1  # seconds
    
    # Server
    JARVIS_SERVER_URL = "http://localhost:5000"
