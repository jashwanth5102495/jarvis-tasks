"""
workflow_state.py
=================
Workflow lifecycle state machine.

A Workflow is a named, multi-stage execution unit.
Each stage contains one or more WorkflowStep objects.
Steps carry dependency declarations, executor assignments,
and full execution history.

State transitions
-----------------
  PENDING → RUNNING → COMPLETED
                    ↘ FAILED
                    ↘ PARTIALLY_COMPLETED   (some steps failed, others succeeded)
  Any state → CANCELLED  (user denied all remaining steps)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class WorkflowStatus(str, Enum):
    PENDING             = "pending"
    RUNNING             = "running"
    COMPLETED           = "completed"
    FAILED              = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    CANCELLED           = "cancelled"
    SKIPPED             = "skipped"


class StepStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    SUCCESS  = "success"
    FAILED   = "failed"
    SKIPPED  = "skipped"
    DENIED   = "denied"
    BLOCKED  = "blocked"   # dependency not met


# ─────────────────────────────────────────────────────────────────────────────
# WorkflowStep
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WorkflowStep:
    """
    One atomic unit of work inside a workflow.

    Fields
    ------
    step_id      : unique identifier (auto-generated)
    name         : human-readable label
    executor     : which executor handles this step
    action       : action method on the executor
    params       : parameters forwarded to the executor
    risk_level   : used by PermissionManager
    depends_on   : list of step_ids that must succeed before this runs
    stage        : logical grouping (e.g. "setup", "build", "verify")
    output       : captured output after execution
    error        : error message if failed
    status       : current lifecycle status
    started_at   : wall-clock start
    finished_at  : wall-clock finish
    duration_ms  : elapsed time
    executor_ctx : reference to the ExecutionContext used (set at runtime)
    """

    name:         str
    executor:     str
    action:       str
    params:       Dict[str, Any]       = field(default_factory=dict)
    risk_level:   str                  = "low"
    depends_on:   List[str]            = field(default_factory=list)
    stage:        str                  = "main"
    step_id:      str                  = field(default_factory=lambda: str(uuid.uuid4())[:10])
    status:       StepStatus           = StepStatus.PENDING
    output:       Optional[str]        = None
    error:        Optional[str]        = None
    started_at:   Optional[datetime]   = None
    finished_at:  Optional[datetime]   = None
    duration_ms:  Optional[float]      = None
    executor_ctx: Optional[Any]        = None   # ExecutionContext, typed as Any to avoid circular

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def mark_running(self) -> None:
        self.status     = StepStatus.RUNNING
        self.started_at = datetime.now()

    def mark_success(self, output: str = "") -> None:
        self.status      = StepStatus.SUCCESS
        self.output      = output
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_ms = (
                (self.finished_at - self.started_at).total_seconds() * 1000
            )

    def mark_failed(self, error: str) -> None:
        self.status      = StepStatus.FAILED
        self.error       = error
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_ms = (
                (self.finished_at - self.started_at).total_seconds() * 1000
            )

    def mark_skipped(self, reason: str = "") -> None:
        self.status = StepStatus.SKIPPED
        self.error  = reason

    def mark_denied(self) -> None:
        self.status = StepStatus.DENIED

    def mark_blocked(self, reason: str = "") -> None:
        self.status = StepStatus.BLOCKED
        self.error  = reason

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id":     self.step_id,
            "name":        self.name,
            "executor":    self.executor,
            "action":      self.action,
            "params":      self.params,
            "risk_level":  self.risk_level,
            "depends_on":  self.depends_on,
            "stage":       self.stage,
            "status":      self.status.value,
            "output":      self.output,
            "error":       self.error,
            "started_at":  self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
        }


# ─────────────────────────────────────────────────────────────────────────────
# WorkflowState
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WorkflowState:
    """
    Complete runtime state of one workflow execution.

    Created by WorkflowOrchestrator at the start of each run.
    Mutated in-place as steps execute.
    Persisted to MongoDB + JSONL log on completion.
    """

    workflow_id:   str
    workflow_name: str
    goal_text:     str
    steps:         List[WorkflowStep]          = field(default_factory=list)
    status:        WorkflowStatus              = WorkflowStatus.PENDING
    started_at:    Optional[datetime]          = None
    finished_at:   Optional[datetime]          = None
    duration_ms:   Optional[float]             = None
    error:         Optional[str]               = None
    metadata:      Dict[str, Any]              = field(default_factory=dict)

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def success_steps(self) -> List[WorkflowStep]:
        return [s for s in self.steps if s.status == StepStatus.SUCCESS]

    @property
    def failed_steps(self) -> List[WorkflowStep]:
        return [s for s in self.steps if s.status == StepStatus.FAILED]

    @property
    def denied_steps(self) -> List[WorkflowStep]:
        return [s for s in self.steps if s.status == StepStatus.DENIED]

    @property
    def skipped_steps(self) -> List[WorkflowStep]:
        return [s for s in self.steps if s.status in (StepStatus.SKIPPED, StepStatus.BLOCKED)]

    @property
    def pending_steps(self) -> List[WorkflowStep]:
        return [s for s in self.steps if s.status == StepStatus.PENDING]

    @property
    def stages(self) -> List[str]:
        seen, result = set(), []
        for s in self.steps:
            if s.stage not in seen:
                seen.add(s.stage)
                result.append(s.stage)
        return result

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def get_steps_by_stage(self, stage: str) -> List[WorkflowStep]:
        return [s for s in self.steps if s.stage == stage]

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def mark_running(self) -> None:
        self.status     = WorkflowStatus.RUNNING
        self.started_at = datetime.now()

    def mark_finished(self) -> None:
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_ms = (
                (self.finished_at - self.started_at).total_seconds() * 1000
            )
        failed  = len(self.failed_steps)
        success = len(self.success_steps)
        total   = len(self.steps)

        if failed == 0 and success > 0:
            self.status = WorkflowStatus.COMPLETED
        elif failed > 0 and success > 0:
            self.status = WorkflowStatus.PARTIALLY_COMPLETED
        elif failed == total:
            self.status = WorkflowStatus.FAILED
        else:
            self.status = WorkflowStatus.COMPLETED

    def mark_cancelled(self) -> None:
        self.status      = WorkflowStatus.CANCELLED
        self.finished_at = datetime.now()

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id":   self.workflow_id,
            "workflow_name": self.workflow_name,
            "goal_text":     self.goal_text,
            "status":        self.status.value,
            "started_at":    self.started_at.isoformat() if self.started_at else None,
            "finished_at":   self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms":   self.duration_ms,
            "error":         self.error,
            "metadata":      self.metadata,
            "steps":         [s.to_dict() for s in self.steps],
            "summary": {
                "total":   len(self.steps),
                "success": len(self.success_steps),
                "failed":  len(self.failed_steps),
                "denied":  len(self.denied_steps),
                "skipped": len(self.skipped_steps),
            },
        }
