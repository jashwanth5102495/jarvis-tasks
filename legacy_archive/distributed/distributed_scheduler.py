
"""
distributed_scheduler.py
=======================
Distributed scheduling system for background and timed workflows.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json

from distributed.node_registry import node_registry
from distributed.device_router import device_router
from distributed.remote_executor import remote_executor

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    task_id: str
    workflow: Dict[str, Any]
    target_node_id: Optional[str]
    schedule_type: str  # "once", "recurring"
    next_run: datetime
    interval: Optional[timedelta] = None
    last_run: Optional[datetime] = None
    is_active: bool = True


class DistributedScheduler:
    """
    Schedules workflows for execution on remote nodes.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "scheduled_tasks.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, ScheduledTask] = {}
        self._load()

    def schedule_once(self, workflow: Dict[str, Any], run_at: datetime,
                      target_node_id: Optional[str] = None) -> str:
        """Schedule a workflow to run once at a specific time."""
        import uuid
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            task_id=task_id, workflow=workflow, target_node_id=target_node_id,
            schedule_type="once", next_run=run_at)
        self._tasks[task_id] = task
        self._save()
        logger.info(f"Scheduled one-time task {task_id} for {run_at}")
        return task_id

    def schedule_recurring(self, workflow: Dict[str, Any], interval: timedelta,
                           start_at: Optional[datetime] = None,
                           target_node_id: Optional[str] = None) -> str:
        """Schedule a recurring workflow."""
        import uuid
        task_id = str(uuid.uuid4())
        next_run = start_at or datetime.now() + interval
        task = ScheduledTask(
            task_id=task_id, workflow=workflow, target_node_id=target_node_id,
            schedule_type="recurring", next_run=next_run, interval=interval)
        self._tasks[task_id] = task
        self._save()
        logger.info(f"Scheduled recurring task {task_id} every {interval}")
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id in self._tasks:
            self._tasks[task_id].is_active = False
            self._save()
            logger.info(f"Cancelled task {task_id}")
            return True
        return False

    def get_due_tasks(self) -> List[ScheduledTask]:
        """Get all tasks that are due to run."""
        now = datetime.now()
        due_tasks = []
        for task in self._tasks.values():
            if task.is_active and task.next_run <= now:
                due_tasks.append(task)
        return due_tasks

    def execute_due_tasks(self) -> List[str]:
        """Execute all tasks that are due to run."""
        due_tasks = self.get_due_tasks()
        execution_ids = []
        for task in due_tasks:
            try:
                execution_id = remote_executor.execute_remotely(task.workflow, task.target_node_id)
                execution_ids.append(execution_id)
                task.last_run = datetime.now()
                if task.schedule_type == "once":
                    task.is_active = False
                elif task.interval:
                    task.next_run = datetime.now() + task.interval
                logger.info(f"Executed task {task.task_id}")
            except Exception as e:
                logger.error(f"Failed to execute task {task.task_id}: {e}")
        self._save()
        return execution_ids

    def list_tasks(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """List all scheduled tasks."""
        tasks = list(self._tasks.values())
        if only_active:
            tasks = [t for t in tasks if t.is_active]
        return [
            {
                "task_id": t.task_id,
                "schedule_type": t.schedule_type,
                "next_run": t.next_run.isoformat(),
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "is_active": t.is_active
            }
            for t in tasks
        ]

    def _save(self) -> None:
        data = {
            "tasks": [
                {
                    "task_id": t.task_id,
                    "workflow": t.workflow,
                    "target_node_id": t.target_node_id,
                    "schedule_type": t.schedule_type,
                    "next_run": t.next_run.isoformat(),
                    "interval_seconds": t.interval.total_seconds() if t.interval else None,
                    "last_run": t.last_run.isoformat() if t.last_run else None,
                    "is_active": t.is_active
                }
                for t in self._tasks.values()
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
            for t_data in data.get("tasks", []):
                interval = timedelta(seconds=t_data["interval_seconds"]) if t_data.get("interval_seconds") else None
                task = ScheduledTask(
                    task_id=t_data["task_id"],
                    workflow=t_data["workflow"],
                    target_node_id=t_data.get("target_node_id"),
                    schedule_type=t_data["schedule_type"],
                    next_run=datetime.fromisoformat(t_data["next_run"]),
                    interval=interval,
                    last_run=datetime.fromisoformat(t_data["last_run"]) if t_data.get("last_run") else None,
                    is_active=t_data["is_active"])
                self._tasks[task.task_id] = task
            logger.info(f"Loaded {len(self._tasks)} scheduled tasks")
        except Exception as e:
            logger.error(f"Failed to load scheduled tasks: {e}")


# Module-level singleton
distributed_scheduler = DistributedScheduler()
