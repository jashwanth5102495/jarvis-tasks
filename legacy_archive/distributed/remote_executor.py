
"""
remote_executor.py
==================
Remote workflow execution system for JARVIS.
Sends workflows to remote nodes for execution.
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from distributed.node_registry import node_registry
from distributed.auth_manager import auth_manager
from distributed.encrypted_transport import encrypted_transport
from distributed.device_router import device_router

logger = logging.getLogger(__name__)


@dataclass
class RemoteExecution:
    """Tracks a remote workflow execution."""
    execution_id: str
    workflow: Dict[str, Any]
    target_node_id: str
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RemoteExecutor:
    """
    Manages remote execution of workflows on other nodes.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "remote_executions.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._executions: Dict[str, RemoteExecution] = {}
        self._load()

    def execute_remotely(
        self, workflow: Dict[str, Any], target_node_id: Optional[str] = None) -> str:
        """
        Execute a workflow on a remote node.
        Returns the execution ID.
        """
        # Select the target node if not specified
        if not target_node_id:
            node = device_router.select_node_for_workflow(workflow)
            if not node:
                raise RuntimeError("No suitable node found")
            target_node_id = node.node_id

        execution_id = str(uuid.uuid4())
        execution = RemoteExecution(
            execution_id=execution_id, workflow=workflow, target_node_id=target_node_id, status="pending")

        self._executions[execution_id] = execution
        self._save()

        # Prepare and send the execution request
        self._send_execution_request(execution)
        logger.info(f"Started remote execution {execution_id} on node {target_node_id}")
        return execution_id

    def _send_execution_request(self, execution: RemoteExecution) -> None:
        """Send a remote execution request to target node."""
        payload = {
            "type": "execute_workflow",
            "execution_id": execution.execution_id,
            "workflow": execution.workflow
        }

        # In a real implementation, this sends over encrypted transport
        # For now, mock by updating status
        execution.status = "running"
        execution.started_at = datetime.now()
        self._save()

    def update_execution_status(self, execution_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> bool:
        """Update the status of a remote execution."""
        if execution_id not in self._executions:
            logger.warning(f"Execution not found: {execution_id}")
            return False

        execution = self._executions[execution_id]
        execution.status = status
        if result:
            execution.result = result
        if error:
            execution.error = error
        if status == "completed":
            execution.completed_at = datetime.now()
        self._save()
        logger.info(f"Updated execution {execution_id} status to {status}")
        return True

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a remote execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return None
        return {
            "execution_id": execution.execution_id,
            "status": execution.status,
            "target_node_id": execution.target_node_id,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "result": execution.result,
            "error": execution.error
        }

    def list_executions(self, node_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List remote executions, optionally filtered."""
        executions = list(self._executions.values())
        if node_id:
            executions = [e for e in executions if e.target_node_id == node_id]
        if status:
            executions = [e for e in executions if e.status == status]
        return [
            {
                "execution_id": e.execution_id,
                "status": e.status,
                "target_node_id": e.target_node_id
            }
            for e in executions
        ]

    def _save(self) -> None:
        """Save remote executions to disk."""
        data = {
            "executions": [
                {
                    "execution_id": e.execution_id,
                    "workflow": e.workflow,
                    "target_node_id": e.target_node_id,
                    "status": e.status,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "result": e.result,
                    "error": e.error
                }
                for e in self._executions.values()
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load remote executions from disk."""
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            for e_data in data.get("executions", []):
                execution = RemoteExecution(
                    execution_id=e_data["execution_id"],
                    workflow=e_data["workflow"],
                    target_node_id=e_data["target_node_id"],
                    status=e_data["status"],
                    started_at=datetime.fromisoformat(e_data["started_at"]) if e_data.get("started_at") else None,
                    completed_at=datetime.fromisoformat(e_data["completed_at"]) if e_data.get("completed_at") else None,
                    result=e_data.get("result"),
                    error=e_data.get("error")
                )
                self._executions[execution.execution_id] = execution
            logger.info(f"Loaded {len(self._executions)} remote executions")
        except Exception as e:
            logger.error(f"Failed to load remote executions: {e}")


# Module-level singleton
remote_executor = RemoteExecutor()
