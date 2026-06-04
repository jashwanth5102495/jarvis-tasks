
"""
sync_engine.py
=============
Multi-device memory synchronization engine.
Synchronizes workflows, projects, preferences, and execution state.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from memory.project_memory import project_memory
from memory.preference_memory import preference_memory
from memory.workflow_checkpoint import workflow_checkpoint
from memory.execution_history import execution_history

logger = logging.getLogger(__name__)


@dataclass
class SyncOperation:
    """Represents a synchronization operation."""
    sync_id: str
    operation_type: str  # "push", "pull", "conflict"
    data_type: str  # "projects", "preferences", "workflows"
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class SyncEngine:
    """
    Synchronizes memory across multiple JARVIS nodes.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "sync_logs.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._sync_history: List[SyncOperation] = []
        self._last_sync: Optional[datetime] = None
        self._load()

    def push_changes(self, data_type: str) -> SyncOperation:
        """Push local changes to remote."""
        sync_id = f"push_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        operation = SyncOperation(
            sync_id=sync_id, operation_type="push", data_type=data_type,
            status="in_progress", started_at=datetime.now())
        self._sync_history.append(operation)
        self._save()
        logger.info(f"Starting push for {data_type}")

        # Mock implementation
        try:
            operation.status = "completed"
            operation.completed_at = datetime.now()
            self._last_sync = datetime.now()
            self._save()
            logger.info(f"Push completed for {data_type}")
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            self._save()
            logger.error(f"Push failed for {data_type}: {e}")
        return operation

    def pull_changes(self, data_type: str) -> SyncOperation:
        """Pull remote changes to local."""
        sync_id = f"pull_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        operation = SyncOperation(
            sync_id=sync_id, operation_type="pull", data_type=data_type,
            status="in_progress", started_at=datetime.now())
        self._sync_history.append(operation)
        self._save()
        logger.info(f"Starting pull for {data_type}")

        # Mock implementation
        try:
            operation.status = "completed"
            operation.completed_at = datetime.now()
            self._last_sync = datetime.now()
            self._save()
            logger.info(f"Pull completed for {data_type}")
        except Exception as e:
            operation.status = "failed"
            operation.error = str(e)
            self._save()
            logger.error(f"Pull failed for {data_type}: {e}")
        return operation

    def sync_all(self) -> List[SyncOperation]:
        """Synchronize all data types."""
        data_types = ["projects", "preferences", "workflows", "execution_history"]
        operations = []
        for data_type in data_types:
            # First pull, then push
            operations.append(self.pull_changes(data_type))
            operations.append(self.push_changes(data_type))
        return operations

    def get_last_sync(self) -> Optional[datetime]:
        """Get the timestamp of the last successful sync."""
        return self._last_sync

    def get_sync_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent sync history."""
        history = self._sync_history[-limit:]
        return [
            {
                "sync_id": op.sync_id,
                "operation_type": op.operation_type,
                "data_type": op.data_type,
                "status": op.status,
                "started_at": op.started_at.isoformat() if op.started_at else None,
                "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                "error": op.error
            }
            for op in history
        ]

    def _save(self) -> None:
        """Save sync history to disk."""
        data = {
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "sync_history": [
                {
                    "sync_id": op.sync_id,
                    "operation_type": op.operation_type,
                    "data_type": op.data_type,
                    "status": op.status,
                    "started_at": op.started_at.isoformat() if op.started_at else None,
                    "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                    "error": op.error
                }
                for op in self._sync_history
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load sync history from disk."""
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            self._last_sync = datetime.fromisoformat(data["last_sync"]) if data.get("last_sync") else None
            for op_data in data.get("sync_history", []):
                operation = SyncOperation(
                    sync_id=op_data["sync_id"],
                    operation_type=op_data["operation_type"],
                    data_type=op_data["data_type"],
                    status=op_data["status"],
                    started_at=datetime.fromisoformat(op_data["started_at"]) if op_data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(op_data["completed_at"]) if op_data.get("completed_at") else None,
                    error=op_data.get("error")
                )
                self._sync_history.append(operation)
            logger.info(f"Loaded {len(self._sync_history)} sync operations")
        except Exception as e:
            logger.error(f"Failed to load sync history: {e}")


# Module-level singleton
sync_engine = SyncEngine()
