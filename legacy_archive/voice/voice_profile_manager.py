
"""
voice_profile_manager.py
========================
Voice profile management system for JARVIS.
Loads, saves, and switches voice profiles.
"""

import logging
from pathlib import Path
import json
from typing import Optional

logger = logging.getLogger(__name__)


DEFAULT_PROFILES = {
    "jarvis_classic": {
        "engine": "piper",
        "voice": "en_GB-alan-medium",
        "speed": 1.0,
        "volume": 1.0,
        "tone": "calm"
    },
    "professional": {
        "engine": "piper",
        "voice": "en_US-lessac-medium",
        "speed": 1.0,
        "volume": 1.0,
        "tone": "professional"
    },
    "friendly": {
        "engine": "piper",
        "voice": "en_US-amy-medium",
        "speed": 1.0,
        "volume": 1.0,
        "tone": "friendly"
    },
    "technical": {
        "engine": "piper",
        "voice": "en_US-ryan-high",
        "speed": 1.1,
        "volume": 1.0,
        "tone": "technical"
    }
}


class VoiceProfileManager:
    def __init__(self, profiles_path: Optional[Path] = None):
        self.profiles_path = profiles_path or (
            Path(__file__).parent.parent / "config" / "voice_profiles.json"
        )
        self.profiles = {}
        self.current_profile_name = "jarvis_classic"
        self._load_profiles()

    def _load_profiles(self):
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
                logger.info(f"Loaded {len(self.profiles)} voice profiles")
            except Exception as e:
                logger.warning(f"Failed to load profiles, using defaults: {e}")
                self.profiles = DEFAULT_PROFILES
                self._save_profiles()
        else:
            self.profiles = DEFAULT_PROFILES
            self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_profiles()

    def _save_profiles(self):
        try:
            with open(self.profiles_path, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=4)
            logger.info("Voice profiles saved")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")

    def get_current_profile(self) -> dict:
        return self.profiles.get(self.current_profile_name, DEFAULT_PROFILES["jarvis_classic"])

    def get_profile(self, name: str) -> Optional[dict]:
        return self.profiles.get(name)

    def set_profile(self, name: str) -> bool:
        if name in self.profiles:
            self.current_profile_name = name
            logger.info(f"Switched to voice profile: {name}")
            return True
        else:
            logger.warning(f"Unknown profile: {name}")
            return False

    def list_profiles(self) -> list:
        return list(self.profiles.keys())

    def create_profile(self, name: str, config: dict):
        self.profiles[name] = config
        self._save_profiles()

    def delete_profile(self, name: str) -> bool:
        if name not in ["jarvis_classic", "professional", "friendly", "technical"]:
            if name in self.profiles:
                del self.profiles[name]
                self._save_profiles()
                return True
        else:
            logger.warning(f"Cannot delete default profile: {name}")
        return False


# Module-level singleton
voice_profile_manager = VoiceProfileManager()

