"""
action_queue.py
===============
ActionQueue — sequential execution queue for desktop control actions.

Responsibilities
----------------
- Hold a list of ControlActions in order
- Execute them one-by-one through the ControlManager
- Support delay between actions
- Support retry on failure (configurable per-action)
- Emergency stop: drains the queue immediately
- Persist completed/failed actions to the control log

States
------
  PENDING → RUNNING → SUCCESS / FAILED / DENIED / CANCELLED

Usage
-----
    queue = ActionQueue()
    queue.enqueue(action1)
    queue.enqueue(action2)
    results = queue.run(executor_fn)
"""

from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from typing import Callable, Deque, List, Optional

from computer_control.cc_models import ActionStatus, ControlAction, ControlResult
from computer_control.failsafe import FailSafeTriggered, failsafe

logger = logging.getLogger(__name__)

# Default delay between consecutive actions (seconds)
DEFAULT_ACTION_DELAY_S = 0.3
# Default max retries on transient failure
DEFAULT_MAX_RETRIES = 1


class ActionQueue:
    """
    Sequential action queue with fail-safe, retry, and delay support.

    Parameters
    ----------
    action_delay_s : float
        Seconds to wait between actions.
    max_retries : int
        How many times to retry a failed action before giving up.
    """

    def __init__(
        self,
        action_delay_s: float = DEFAULT_ACTION_DELAY_S,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._queue:         Deque[ControlAction] = deque()
        self._completed:     List[ControlAction]  = []
        self._action_delay:  float                = action_delay_s
        self._max_retries:   int                  = max_retries
        self._running:       bool                 = False

    # ── Queue management ───────────────────────────────────────────────────────

    def enqueue(self, action: ControlAction) -> None:
        """Add an action to the end of the queue."""
        self._queue.append(action)
        logger.debug(f"ActionQueue: enqueued {action}")

    def enqueue_all(self, actions: List[ControlAction]) -> None:
        for a in actions:
            self.enqueue(a)

    def clear(self) -> None:
        """Drain the queue without executing (emergency clear)."""
        count = len(self._queue)
        self._queue.clear()
        logger.info(f"ActionQueue: cleared {count} pending actions")

    def pending_count(self) -> int:
        return len(self._queue)

    def completed_count(self) -> int:
        return len(self._completed)

    # ── Execution ──────────────────────────────────────────────────────────────

    def run(
        self,
        executor_fn: Callable[[ControlAction], str],
        session_id: str = "",
        goal: str = "",
    ) -> ControlResult:
        """
        Execute all queued actions sequentially.

        Parameters
        ----------
        executor_fn : Callable[[ControlAction], str]
            Function that takes a ControlAction and returns an output string.
            Typically ControlManager._dispatch().
        session_id : str
            Identifier for this run (used in ControlResult).
        goal : str
            Human-readable goal description.

        Returns
        -------
        ControlResult with all executed actions.
        """
        result = ControlResult(session_id=session_id, goal=goal)
        self._running = True

        while self._queue and self._running:
            # Check fail-safe before every action
            try:
                failsafe.check()
            except FailSafeTriggered as exc:
                logger.critical(f"ActionQueue: fail-safe triggered — draining queue")
                # Mark all remaining as cancelled
                while self._queue:
                    action = self._queue.popleft()
                    action.mark_cancelled()
                    result.actions.append(action)
                    self._completed.append(action)
                break

            action = self._queue.popleft()
            self._execute_with_retry(action, executor_fn, result)

            # Delay between actions
            if self._queue and self._action_delay > 0:
                time.sleep(self._action_delay)

        self._running = False
        return result

    def stop(self) -> None:
        """Signal the queue to stop after the current action completes."""
        self._running = False
        logger.info("ActionQueue: stop requested")

    # ── Internal ───────────────────────────────────────────────────────────────

    def _execute_with_retry(
        self,
        action: ControlAction,
        executor_fn: Callable[[ControlAction], str],
        result: ControlResult,
    ) -> None:
        attempts = 0
        max_attempts = self._max_retries + 1

        while attempts < max_attempts:
            attempts += 1
            try:
                action.mark_running()
                output = executor_fn(action)
                action.mark_success(output or "")
                logger.info(
                    f"ActionQueue: {action.controller.value}.{action.action} "
                    f"succeeded (attempt {attempts})"
                )
                break

            except FailSafeTriggered:
                action.mark_cancelled()
                logger.critical("ActionQueue: fail-safe during action execution")
                break

            except Exception as exc:
                err = str(exc)
                if attempts < max_attempts:
                    logger.warning(
                        f"ActionQueue: {action.action} failed (attempt {attempts}), "
                        f"retrying… error={err}"
                    )
                    time.sleep(0.5 * attempts)   # back-off
                else:
                    action.mark_failed(err)
                    logger.error(
                        f"ActionQueue: {action.action} failed after "
                        f"{attempts} attempt(s): {err}"
                    )

        result.actions.append(action)
        self._completed.append(action)

    # ── History ────────────────────────────────────────────────────────────────

    def get_completed(self) -> List[ControlAction]:
        return list(self._completed)

    def get_failed(self) -> List[ControlAction]:
        return [a for a in self._completed if a.status == ActionStatus.FAILED]

    def summary(self) -> dict:
        return {
            "total":     len(self._completed),
            "success":   sum(1 for a in self._completed if a.status == ActionStatus.SUCCESS),
            "failed":    sum(1 for a in self._completed if a.status == ActionStatus.FAILED),
            "denied":    sum(1 for a in self._completed if a.status == ActionStatus.DENIED),
            "cancelled": sum(1 for a in self._completed if a.status == ActionStatus.CANCELLED),
        }
