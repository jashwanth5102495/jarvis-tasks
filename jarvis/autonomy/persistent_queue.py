
"""
persistent_queue.py
===================
Persistent task queue that survives restart, crash, and shutdown.
Uses JSON file storage for simplicity.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_QUEUE_FILE = Path(__file__).parent.parent / "config" / "task_queue.json"


class PersistentQueue:
    """
    Simple persistent task queue.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or _QUEUE_FILE
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._queue: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        try:
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load task queue: {e}")
        return []

    def _save(self) -> None:
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._queue, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save task queue: {e}")

    def enqueue(self, task: Dict[str, Any]) -> None:
        task["task_id"] = task.get("task_id", str(datetime.now().timestamp()))
        task["enqueued_at"] = datetime.now().isoformat()
        task["status"] = "pending"
        task["retries"] = 0
        self._queue.append(task)
        self._save()
        logger.info(f"Enqueued task: {task['task_id']}")

    def dequeue(self) -> Optional[Dict[str, Any]]:
        if self._queue:
            task = self._queue.pop(0)
            task["status"] = "running"
            self._save()
            logger.info(f"Dequeued task: {task['task_id']}")
            return task
        return None

    def peek(self) -> Optional[Dict[str, Any]]:
        if self._queue:
            return self._queue[0]
        return None

    def mark_complete(self, task_id: str) -> None:
        for task in self._queue:
            if task["task_id"] == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                self._save()
                logger.info(f"Marked task {task_id} as complete")
                return

    def mark_failed(self, task_id: str, error: str, max_retries: int = 3) -> None:
        for i, task in enumerate(self._queue):
            if task["task_id"] == task_id:
                task["status"] = "failed"
                task["error"] = error
                task["failed_at"] = datetime.now().isoformat()
                task["retries"] += 1
                if task["retries"] < max_retries:
                    # Re-enqueue at the end for retry
                    task["status"] = "pending"
                    self._queue.append(self._queue.pop(i))
                self._save()
                logger.warning(f"Marked task {task_id} as failed (retries: {task['retries']})")
                return

    def list_all(self) -> List[Dict[str, Any]]:
        return self._queue.copy()


persistent_queue = PersistentQueue()
