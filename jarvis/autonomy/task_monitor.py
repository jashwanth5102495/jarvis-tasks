
"""
task_monitor.py
===============
Monitors task execution, logs progress, and handles timeouts.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TaskMonitor:
    """
    Monitors task execution.
    """

    def __init__(self):
        self._active_tasks: Dict[str, Dict[str, Any]] = {}

    def start_task(self, task_id: str, task_name: str) -> None:
        self._active_tasks[task_id] = {
            "task_id": task_id,
            "task_name": task_name,
            "started_at": datetime.now(),
            "status": "running",
        }
        logger.info(f"Started task {task_id}: {task_name}")

    def end_task(self, task_id: str, status: str = "completed", error: Optional[str] = None) -> None:
        if task_id in self._active_tasks:
            self._active_tasks[task_id]["status"] = status
            self._active_tasks[task_id]["ended_at"] = datetime.now()
            self._active_tasks[task_id]["duration_seconds"] = (
                self._active_tasks[task_id]["ended_at"] - self._active_tasks[task_id]["started_at"]
            ).total_seconds()
            self._active_tasks[task_id]["error"] = error
            logger.info(
                f"Ended task {task_id}: {status} (duration: {self._active_tasks[task_id]['duration_seconds']:.2f}s)"
            )

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        return self._active_tasks.copy()


task_monitor = TaskMonitor()
