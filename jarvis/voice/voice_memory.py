
"""
voice_memory.py
=============
Voice memory system for JARVIS. Stores conversation history,
user preferences, and voice interaction patterns.
"""

from __future__ import annotations

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VoiceInteraction:
    """A single voice interaction."""
    timestamp: datetime
    role: str  # "user" or "assistant"
    content: str
    confidence: float = 1.0


class VoiceMemory:
    """
    Memory system for voice interactions.
    Stores conversation history, user preferences, and voice patterns.
    """

    def __init__(self):
        self._storage_path = Path(__file__).parent.parent / "data" / "voice_memory"
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._interactions: List[VoiceInteraction] = []
        self._user_preferences: Dict[str, Any] = {}
        self._load()

    def add_interaction(self, content: str, role: str, confidence: float = 1.0) -> None:
        """Add a voice interaction to memory."""
        interaction = VoiceInteraction(
            timestamp=datetime.now(),
            role=role,
            content=content,
            confidence=confidence
        )
        
        self._interactions.append(interaction)
        self._save()
        logger.debug(f"Added interaction: {role} - {content[:50]}...")

    def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent voice interactions."""
        recent = self._interactions[-limit:]
        return [
            {
                "timestamp": i.timestamp.isoformat(),
                "role": i.role,
                "content": i.content,
                "confidence": i.confidence
            }
            for i in recent
        ]

    def get_conversation_history(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get conversation history since a given time."""
        interactions = self._interactions
        if since:
            interactions = [i for i in interactions if i.timestamp >= since]
        
        return [
            {
                "timestamp": i.timestamp.isoformat(),
                "role": i.role,
                "content": i.content
            }
            for i in interactions
        ]

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        self._user_preferences[key] = value
        self._save()
        logger.info(f"Set preference: {key} = {value}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self._user_preferences.get(key, default)

    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences."""
        return self._user_preferences.copy()

    def _save(self) -> None:
        """Save voice memory to disk."""
        data = {
            "interactions": [
                {
                    "timestamp": i.timestamp.isoformat(),
                    "role": i.role,
                    "content": i.content,
                    "confidence": i.confidence
                }
                for i in self._interactions[-1000:]  # Keep last 1000 interactions
            ],
            "preferences": self._user_preferences
        }
        
        file_path = self._storage_path / "voice_memory.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load voice memory from disk."""
        file_path = self._storage_path / "voice_memory.json"
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                self._interactions = [
                    VoiceInteraction(
                        timestamp=datetime.fromisoformat(i["timestamp"]),
                        role=i["role"],
                        content=i["content"],
                        confidence=i.get("confidence", 1.0)
                    )
                    for i in data.get("interactions", [])
                ]
                
                self._user_preferences = data.get("preferences", {})
                logger.info(f"Loaded {len(self._interactions)} voice interactions")
            except Exception as e:
                logger.error(f"Failed to load voice memory: {e}")

    def clear(self) -> None:
        """Clear all voice memory."""
        self._interactions = []
        self._user_preferences = {}
        self._save()
        logger.info("Voice memory cleared")


# Module-level singleton
voice_memory = VoiceMemory()

