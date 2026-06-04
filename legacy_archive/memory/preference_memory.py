
"""
preference_memory.py
====================
Persistent storage of user preferences:
  - Preferred browser
  - Preferred IDE
  - Coding style
  - Favorite frameworks
  - Workflow preferences
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_PREFERENCES_FILE = Path(__file__).parent.parent / "config" / "preferences.json"

_DEFAULT_PREFERENCES: Dict[str, Any] = {
    "preferred_browser": "chrome",
    "preferred_ide": "vscode",
    "coding_style": "pep8",
    "favorite_frameworks": ["flask", "react"],
    "theme": "dark",
    "workflow_preferences": {
        "auto_approve_safe_actions": True,
        "show_detailed_logs": False,
    },
}


class PreferenceMemory:
    """
    Persistent user preference manager.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or _PREFERENCES_FILE
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._preferences: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {**_DEFAULT_PREFERENCES, **data}
        except Exception as e:
            logger.warning(f"Failed to load preferences, using defaults: {e}")
        return _DEFAULT_PREFERENCES.copy()

    def _save(self) -> None:
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._preferences.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._preferences[key] = value
        self._save()
        logger.info(f"Set preference {key} to {value}")

    def get_all(self) -> Dict[str, Any]:
        return self._preferences.copy()


preference_memory = PreferenceMemory()
