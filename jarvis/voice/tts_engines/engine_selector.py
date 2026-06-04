
"""
engine_selector.py
===================
Engine selector that picks the best available TTS engine for JARVIS.
"""

import logging
from typing import Optional

from .base_engine import TTSEngine
from .piper_engine import PiperTTSEngine
from .pyttsx3_engine import Pyttsx3TTSEngine

logger = logging.getLogger(__name__)


class TTSEngineSelector:
    def __init__(self):
        self.engines = {}
        self.current_engine: Optional[TTSEngine] = None
        self._register_engines()

    def _register_engines(self):
        # Register all available engines
        self.engines["piper"] = PiperTTSEngine
        self.engines["pyttsx3"] = Pyttsx3TTSEngine

    def get_engine(self, engine_name: Optional[str] = None, config: Optional[dict] = None) -> Optional[TTSEngine]:
        if engine_name and engine_name in self.engines:
            # Try to use specified engine
            engine = self.engines[engine_name](config)
            if engine.initialize():
                logger.info(f"Using TTS engine: {engine_name}")
                self.current_engine = engine
                return engine
            else:
                logger.warning(f"Failed to initialize {engine_name}, falling back...")

        # Try Piper first, then pyttsx3
        for name in ["piper", "pyttsx3"]:
            engine = self.engines[name](config)
            if engine.initialize():
                logger.info(f"Using TTS engine: {name}")
                self.current_engine = engine
                return engine

        logger.error("No TTS engines available!")
        return None


# Module-level singleton
engine_selector = TTSEngineSelector()

