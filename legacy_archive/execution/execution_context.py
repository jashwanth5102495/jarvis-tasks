"""
execution_context.py
====================
Immutable snapshot of a single executor action.
Passed through the entire execution pipeline so every layer
(permissions, sandbox, logging) has full context.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionStatus(str, Enum):
    PENDING    = "pending"
    APPROVED   = "approved"
    DENIED     = "denied"
    RUNNING    = "running"
    SUCCESS    = "success"
    FAILED     = "failed"
    SKIPPED    = "skipped"
    SANDBOXED  = "sandboxed"


class RiskLevel(str, Enum):
    SAFE      = "safe"       # read-only, no side-effects
    LOW       = "low"        # creates files, reversible
    MEDIUM    = "medium"     # modifies files, runs scripts
    HIGH      = "high"       # installs packages, network calls
    CRITICAL  = "critical"   # deletes files, system commands


@dataclass
class ExecutionContext:
    """
    Represents one atomic execution step.

    Fields
    ------
    task_id      : unique ID for the parent task (shared across all steps)
    step_id      : unique ID for this specific step
    executor     : name of the executor handling this step  (e.g. "file")
    action       : specific action within the executor      (e.g. "create_file")
    params       : arbitrary key-value parameters for the action
    risk_level   : assessed risk of this action
    status       : lifecycle status
    output       : captured stdout / return value
    error        : error message if failed
    started_at   : wall-clock start time
    finished_at  : wall-clock finish time
    duration_ms  : elapsed milliseconds
    approved_by  : "user" | "auto" | None
    """

    task_id:     str
    executor:    str
    action:      str
    params:      Dict[str, Any]         = field(default_factory=dict)
    risk_level:  RiskLevel              = RiskLevel.SAFE
    step_id:     str                    = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status:      ExecutionStatus        = ExecutionStatus.PENDING
    output:      Optional[str]          = None
    error:       Optional[str]          = None
    started_at:  Optional[datetime]     = None
    finished_at: Optional[datetime]     = None
    duration_ms: Optional[float]        = None
    approved_by: Optional[str]          = None

    # ── Lifecycle helpers ─────────────────────────────────────────────

    def mark_running(self) -> None:
        self.status     = ExecutionStatus.RUNNING
        self.started_at = datetime.now()

    def mark_success(self, output: str = "") -> None:
        self.status      = ExecutionStatus.SUCCESS
        self.output      = output
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_ms = (
                (self.finished_at - self.started_at).total_seconds() * 1000
            )

    def mark_failed(self, error: str) -> None:
        self.status      = ExecutionStatus.FAILED
        self.error       = error
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_ms = (
                (self.finished_at - self.started_at).total_seconds() * 1000
            )

    def mark_denied(self) -> None:
        self.status = ExecutionStatus.DENIED

    def mark_skipped(self, reason: str = "") -> None:
        self.status = ExecutionStatus.SKIPPED
        self.error  = reason

    # ── Serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id":     self.task_id,
            "step_id":     self.step_id,
            "executor":    self.executor,
            "action":      self.action,
            "params":      self.params,
            "risk_level":  self.risk_level.value,
            "status":      self.status.value,
            "output":      self.output,
            "error":       self.error,
            "started_at":  self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
            "approved_by": self.approved_by,
        }

    def __repr__(self) -> str:
        return (
            f"ExecutionContext("
            f"executor={self.executor!r}, "
            f"action={self.action!r}, "
            f"status={self.status.value}, "
            f"risk={self.risk_level.value})"
        )
