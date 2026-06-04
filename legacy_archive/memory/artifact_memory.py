
"""
artifact_memory.py
==================
Persistent storage of generated artifacts:
  - Files created
  - Screenshots
  - Browser searches
  - Created folders
  - Installed packages
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_ARTIFACTS_FILE = Path(__file__).parent.parent / "config" / "artifacts.json"


class ArtifactMemory:
    """
    Persistent artifact memory manager.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or _ARTIFACTS_FILE
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._artifacts: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        try:
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load artifact memory: {e}")
        return []

    def _save(self) -> None:
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._artifacts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save artifact memory: {e}")

    def add_artifact(
        self,
        artifact_type: str,
        path: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry = {
            "artifact_type": artifact_type,
            "path": path,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._artifacts.append(entry)
        self._save()
        logger.info(f"Added artifact to memory: {path}")

    def list_artifacts(self, artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if artifact_type:
            return [a for a in self._artifacts if a["artifact_type"] == artifact_type]
        return self._artifacts.copy()

    def get_artifacts_by_path(self, path: str) -> List[Dict[str, Any]]:
        return [a for a in self._artifacts if path in a["path"]]


artifact_memory = ArtifactMemory()
