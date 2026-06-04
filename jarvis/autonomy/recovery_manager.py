
"""
recovery_manager.py
===================
Detects crashes, validates recovery safety, and restores workflow/queue state.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from memory.workflow_checkpoint import workflow_checkpoint
from autonomy.workflow_resumer import workflow_resumer
from autonomy.persistent_queue import persistent_queue

logger = logging.getLogger(__name__)


class RecoveryManager:
    """
    Manages system recovery after crash/shutdown.
    """

    def __init__(self):
        self._workflow_checkpoint = workflow_checkpoint
        self._workflow_resumer = workflow_resumer
        self._persistent_queue = persistent_queue

    def run_recovery_check(self) -> None:
        """
        Run complete recovery check at startup.
        """
        logger.info("Running recovery check...")

        # Check for interrupted workflows
        interrupted_workflows = self._workflow_resumer.get_interrupted_workflows()
        if interrupted_workflows:
            logger.info(f"Found {len(interrupted_workflows)} interrupted workflow(s)")
            for workflow in interrupted_workflows:
                if self._workflow_resumer.prompt_resume(workflow):
                    logger.info(f"Resuming workflow: {workflow.workflow_id}")
                    # TODO: Integrate with WorkflowOrchestrator to resume execution
                    pass
                else:
                    logger.info(f"Discarding workflow: {workflow.workflow_id}")
                    self._workflow_resumer.delete_checkpoint(workflow)

        # Restore persistent queue
        queued_tasks = self._persistent_queue.list_all()
        if queued_tasks:
            logger.info(f"Restored {len(queued_tasks)} queued task(s)")


recovery_manager = RecoveryManager()
