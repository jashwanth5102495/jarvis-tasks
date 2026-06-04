
"""
Persistent Memory Module
=======================
Stores long-term data to disk for persistence across restarts
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class PersistentMemory:
    """Stores long-term memory data to JSON files on disk."""

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent.parent / "data"
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._memories_file = self._storage_path / "persistent_memory.json"
        self._memories: Dict[str, Any] = self._load()
        logger.info("PersistentMemory initialized")

    def _load(self) -> Dict[str, Any]:
        """Load memories from disk."""
        if self._memories_file.exists():
            try:
                with open(self._memories_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load persistent memory: {e}")
                return {}
        return {}

    def _save(self) -> None:
        """Save memories to disk."""
        with open(self._memories_file, "w") as f:
            json.dump(self._memories, f, indent=2, default=str)

    def store(self, key: str, value: Any):
        """Store a key-value pair in persistent memory."""
        self._memories[key] = value
        self._save()
        logger.info(f"Stored in persistent memory: {key}")

    def retrieve(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from persistent memory."""
        return self._memories.get(key, default)

    def delete(self, key: str) -> bool:
        """Delete a key from persistent memory."""
        if key in self._memories:
            del self._memories[key]
            self._save()
            logger.info(f"Deleted from persistent memory: {key}")
            return True
        return False

    def get_all(self) -> Dict[str, Any]:
        """Get all persistent memories."""
        return dict(self._memories)


# Module-level singleton
persistent_memory = PersistentMemory()

