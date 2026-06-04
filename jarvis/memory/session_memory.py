
"""
Session Memory Module
====================
In-memory storage for current session data (tasks, context, etc.)
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SessionTask:
    task_id: str
    user_input: str
    goal: Any
    plan: Any
    execution_result: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)


class SessionMemory:
    """Stores session-specific data in memory."""

    def __init__(self):
        self._tasks: Dict[str, SessionTask] = {}
        self._context: Dict[str, Any] = {}
        logger.info("SessionMemory initialized")

    def add_task(self, task: SessionTask) -> str:
        """Add a task to session memory."""
        self._tasks[task.task_id] = task
        logger.info(f"Added task {task.task_id} to session memory")
        return task.task_id

    def get_task(self, task_id: str) -> Optional[SessionTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[SessionTask]:
        """Get all tasks in current session."""
        return list(self._tasks.values())

    def update_context(self, key: str, value: Any):
        """Update session context."""
        self._context[key] = value
        logger.debug(f"Updated session context: {key} = {value}")

    def get_context(self, key: str) -> Optional[Any]:
        """Get a value from session context."""
        return self._context.get(key)

    def get_all_context(self) -> Dict[str, Any]:
        """Get all session context."""
        return dict(self._context)

    def clear(self):
        """Clear session memory."""
        self._tasks.clear()
        self._context.clear()
        logger.info("Session memory cleared")


# Module-level singleton
session_memory = SessionMemory()

