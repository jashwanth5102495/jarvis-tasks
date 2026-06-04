
"""
workflow_checkpoint.py
======================
Persistent checkpoints for active workflows, allowing recovery from shutdown/crash.
Stores checkpoints in:
  - workflow_state/checkpoint_*.json
  - MongoDB collection "workflow_checkpoints" (best-effort)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from orchestration.workflow_state import WorkflowState, WorkflowStep, WorkflowStatus, StepStatus

logger = logging.getLogger(__name__)

_CHECKPOINT_DIR = Path(__file__).parent.parent / "workflow_state"


def _dict_to_workflow_state(data: Dict[str, Any]) -> WorkflowState:
    steps = []
    for step_data in data.get("steps", []):
        step = WorkflowStep(
            name=step_data["name"],
            executor=step_data["executor"],
            action=step_data["action"],
            params=step_data.get("params", {}),
            risk_level=step_data.get("risk_level", "low"),
            depends_on=step_data.get("depends_on", []),
            stage=step_data.get("stage", "main"),
            step_id=step_data.get("step_id"),
            status=StepStatus(step_data["status"]),
            output=step_data.get("output"),
            error=step_data.get("error"),
        )
        if step_data.get("started_at"):
            step.started_at = datetime.fromisoformat(step_data["started_at"])
        if step_data.get("finished_at"):
            step.finished_at = datetime.fromisoformat(step_data["finished_at"])
        if step_data.get("duration_ms"):
            step.duration_ms = step_data["duration_ms"]
        steps.append(step)

    state = WorkflowState(
        workflow_id=data["workflow_id"],
        workflow_name=data["workflow_name"],
        goal_text=data["goal_text"],
        steps=steps,
        status=WorkflowStatus(data["status"]),
        metadata=data.get("metadata", {}),
    )
    if data.get("started_at"):
        state.started_at = datetime.fromisoformat(data["started_at"])
    if data.get("finished_at"):
        state.finished_at = datetime.fromisoformat(data["finished_at"])
    if data.get("duration_ms"):
        state.duration_ms = data["duration_ms"]
    state.error = data.get("error")
    return state


class WorkflowCheckpoint:
    """
    Manages workflow checkpoints for crash/shutdown recovery.
    """

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        self._checkpoint_dir = checkpoint_dir or _CHECKPOINT_DIR
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, state: WorkflowState) -> None:
        """
        Save a checkpoint of the current workflow state.
        """
        checkpoint_file = self._checkpoint_dir / f"checkpoint_{state.workflow_id}.json"
        try:
            data = state.to_dict()
            data["checkpoint_timestamp"] = datetime.now().isoformat()
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved checkpoint for workflow {state.workflow_id}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Load a checkpoint by workflow ID.
        """
        checkpoint_file = self._checkpoint_dir / f"checkpoint_{workflow_id}.json"
        if not checkpoint_file.exists():
            return None
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded checkpoint for workflow {workflow_id}")
            return _dict_to_workflow_state(data)
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def list_interrupted_workflows(self) -> List[WorkflowState]:
        """
        List all workflows that were interrupted (status RUNNING or PENDING).
        """
        workflows = []
        for checkpoint_file in self._checkpoint_dir.glob("checkpoint_*.json"):
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                state = _dict_to_workflow_state(data)
                if state.status in (WorkflowStatus.RUNNING, WorkflowStatus.PENDING):
                    workflows.append(state)
            except Exception as e:
                logger.warning(f"Failed to load checkpoint file {checkpoint_file}: {e}")
        return workflows

    def delete_checkpoint(self, workflow_id: str) -> None:
        """
        Delete a checkpoint (call after workflow completes successfully).
        """
        checkpoint_file = self._checkpoint_dir / f"checkpoint_{workflow_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"Deleted checkpoint for workflow {workflow_id}")


workflow_checkpoint = WorkflowCheckpoint()
