
"""
remote_memory.py
===============
Remote memory access and distributed memory system.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class RemoteMemoryEntry:
    """Entry in remote memory."""
    key: str
    value: Any
    node_id: str
    version: int = 1
    last_updated: datetime = field(default_factory=datetime.now)


class RemoteMemory:
    """
    Provides access to distributed memory across nodes.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "remote_memory.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._local_cache: Dict[str, RemoteMemoryEntry] = {}
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from remote memory (checks local cache first)."""
        if key in self._local_cache:
            return self._local_cache[key].value
        return default

    def set(self, key: str, value: Any, node_id: str = "local") -> None:
        """Set a value in remote memory."""
        entry = RemoteMemoryEntry(
            key=key, value=value, node_id=node_id,
            version=self._local_cache[key].version + 1 if key in self._local_cache else 1)
        self._local_cache[key] = entry
        self._save()
        logger.info(f"Set remote memory key {key} (version {entry.version})")

    def delete(self, key: str) -> bool:
        """Delete a value from remote memory."""
        if key in self._local_cache:
            del self._local_cache[key]
            self._save()
            logger.info(f"Deleted remote memory key {key}")
            return True
        return False

    def get_for_node(self, node_id: str) -> Dict[str, Any]:
        """Get all memory entries for a specific node."""
        result = {}
        for key, entry in self._local_cache.items():
            if entry.node_id == node_id:
                result[key] = entry.value
        return result

    def list_keys(self) -> List[str]:
        """List all keys in remote memory."""
        return list(self._local_cache.keys())

    def sync_from_node(self, node_id: str, remote_data: Dict[str, Any]) -> None:
        """Sync remote memory from another node."""
        for key, value in remote_data.items():
            existing = self._local_cache.get(key)
            if not existing or (existing and existing.node_id != node_id):
                # Take the newer version
                self._local_cache[key] = RemoteMemoryEntry(
                    key=key, value=value, node_id=node_id,
                    version=existing.version + 1 if existing else 1)
        self._save()
        logger.info(f"Synced {len(remote_data)} entries from node {node_id}")

    def _save(self) -> None:
        data = {
            "entries": [
                {
                    "key": e.key,
                    "value": e.value,
                    "node_id": e.node_id,
                    "version": e.version,
                    "last_updated": e.last_updated.isoformat()
                }
                for e in self._local_cache.values()
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            for entry_data in data.get("entries", []):
                entry = RemoteMemoryEntry(
                    key=entry_data["key"],
                    value=entry_data["value"],
                    node_id=entry_data["node_id"],
                    version=entry_data.get("version", 1),
                    last_updated=datetime.fromisoformat(entry_data["last_updated"]))
                self._local_cache[entry.key] = entry
            logger.info(f"Loaded {len(self._local_cache)} remote memory entries")
        except Exception as e:
            logger.error(f"Failed to load remote memory: {e}")


# Module-level singleton
remote_memory = RemoteMemory()
