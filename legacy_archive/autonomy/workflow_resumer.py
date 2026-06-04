
"""
workflow_resumer.py
===================
Detects interrupted workflows and prompts user to resume them.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from memory.workflow_checkpoint import workflow_checkpoint
from orchestration.workflow_state import WorkflowState

logger = logging.getLogger(__name__)


class WorkflowResumer:
    """
    Manages workflow resumption after shutdown/crash.
    """

    def __init__(self):
        self._checkpoint_manager = workflow_checkpoint

    def get_interrupted_workflows(self) -> List[WorkflowState]:
        """
        Get all workflows that were interrupted.
        """
        return self._checkpoint_manager.list_interrupted_workflows()

    def prompt_resume(self, workflow: WorkflowState) -> bool:
        """
        Prompt user to resume an interrupted workflow (CLI implementation).
        """
        print("\n" + "=" * 60)
        print(f"⚠️  Detected interrupted workflow: {workflow.workflow_name}")
        print(f"   Workflow ID: {workflow.workflow_id}")
        print(f"   Status: {workflow.status.value}")
        print(f"   Goal: {workflow.goal_text}")
        print(f"   Completed steps: {len(workflow.success_steps)}/{len(workflow.steps)}")
        print("=" * 60)

        try:
            while True:
                response = input("Resume this workflow? [Y/n] ").strip().lower()
                if response in ("y", "yes", ""):
                    return True
                elif response in ("n", "no"):
                    return False
        except KeyboardInterrupt:
            return False

    def delete_checkpoint(self, workflow: WorkflowState) -> None:
        """
        Delete checkpoint after workflow is resumed or discarded.
        """
        self._checkpoint_manager.delete_checkpoint(workflow.workflow_id)


workflow_resumer = WorkflowResumer()
