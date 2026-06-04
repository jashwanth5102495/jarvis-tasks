
"""
execution_history.py
====================
Persistent history of all executions:
  - Desktop actions
  - Browser actions
  - Workflow steps
  - Failures
  - Recovery attempts
  - Timestamps
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_EXECUTION_HISTORY_DIR = Path(__file__).parent.parent / "logs" / "execution_history"


class ExecutionHistory:
    """
    Persistent execution history manager.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self._storage_dir = storage_dir or _EXECUTION_HISTORY_DIR
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._history: List[Dict[str, Any]] = []

    def _get_today_file(self) -> Path:
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self._storage_dir / f"{date_str}.jsonl"

    def log_execution(
        self,
        execution_type: str,
        action: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_type": execution_type,
            "action": action,
            "status": status,
            "details": details or {},
            "error": error,
        }
        self._history.append(entry)
        try:
            with open(self._get_today_file(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write execution history: {e}")

    def get_today_history(self) -> List[Dict[str, Any]]:
        history = []
        today_file = self._get_today_file()
        if today_file.exists():
            try:
                with open(today_file, "r", encoding="utf-8") as f:
                    for line in f:
                        history.append(json.loads(line))
            except Exception as e:
                logger.warning(f"Failed to read today's execution history: {e}")
        return history


execution_history = ExecutionHistory()
