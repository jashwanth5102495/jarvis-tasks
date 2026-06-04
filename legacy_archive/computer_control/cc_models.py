"""
cc_models.py
============
Shared data models for the Computer Control layer.

Kept in one file so every module can import without circular deps.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class ActionStatus(str, Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    DENIED    = "denied"
    RUNNING   = "running"
    SUCCESS   = "success"
    FAILED    = "failed"
    CANCELLED = "cancelled"
    SKIPPED   = "skipped"


class ActionRisk(str, Enum):
    """
    SAFE     : screenshot, read screen state — no side-effects
    MEDIUM   : mouse move, scroll, window focus
    HIGH     : click, type text, open app, browser interaction
    CRITICAL : system-level commands — always blocked
    """
    SAFE     = "safe"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class ControllerType(str, Enum):
    MOUSE      = "mouse"
    KEYBOARD   = "keyboard"
    WINDOW     = "window"
    BROWSER    = "browser"
    APP        = "app"
    SCREEN     = "screen"
    SCREENSHOT = "screenshot"
    UI         = "ui"


# ─────────────────────────────────────────────────────────────────────────────
# ControlAction — one atomic desktop action
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ControlAction:
    """
    Represents one atomic desktop control action.

    Fields
    ------
    controller  : which controller handles this (mouse, keyboard, …)
    action      : method name on the controller
    params      : forwarded to the controller method
    risk        : used by PermissionGate
    description : human-readable label shown in the UI
    action_id   : unique ID (auto-generated)
    status      : lifecycle status
    output      : result string after execution
    error       : error message if failed
    started_at  : wall-clock start
    finished_at : wall-clock finish
    duration_ms : elapsed milliseconds
    approved_by : "user" | "auto" | None
    screenshot_before : path to screenshot taken before action
    screenshot_after  : path to screenshot taken after action
    """

    controller:         ControllerType
    action:             str
    params:             Dict[str, Any]       = field(default_factory=dict)
    risk:               ActionRisk           = ActionRisk.MEDIUM
    description:        str                  = ""
    action_id:          str                  = field(default_factory=lambda: str(uuid.uuid4())[:10])
    status:             ActionStatus         = ActionStatus.PENDING
    output:             Optional[str]        = None
    error:              Optional[str]        = None
    started_at:         Optional[datetime]   = None
    finished_at:        Optional[datetime]   = None
    duration_ms:        Optional[float]      = None
    approved_by:        Optional[str]        = None
    screenshot_before:  Optional[str]        = None
    screenshot_after:   Optional[str]        = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def mark_running(self) -> None:
        self.status     = ActionStatus.RUNNING
        self.started_at = datetime.now()

    def mark_success(self, output: str = "") -> None:
        self.status      = ActionStatus.SUCCESS
        self.output      = output
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_ms = (
                (self.finished_at - self.started_at).total_seconds() * 1000
            )

    def mark_failed(self, error: str) -> None:
        self.status      = ActionStatus.FAILED
        self.error       = error
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_ms = (
                (self.finished_at - self.started_at).total_seconds() * 1000
            )

    def mark_denied(self) -> None:
        self.status = ActionStatus.DENIED

    def mark_cancelled(self) -> None:
        self.status = ActionStatus.CANCELLED

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id":          self.action_id,
            "controller":         self.controller.value,
            "action":             self.action,
            "params":             self.params,
            "risk":               self.risk.value,
            "description":        self.description,
            "status":             self.status.value,
            "output":             self.output,
            "error":              self.error,
            "started_at":         self.started_at.isoformat() if self.started_at else None,
            "finished_at":        self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms":        self.duration_ms,
            "approved_by":        self.approved_by,
            "screenshot_before":  self.screenshot_before,
            "screenshot_after":   self.screenshot_after,
        }

    def __repr__(self) -> str:
        return (
            f"ControlAction({self.controller.value}.{self.action}, "
            f"risk={self.risk.value}, status={self.status.value})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# ScreenRegion — bounding box for UI element detection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ScreenRegion:
    x:      int
    y:      int
    width:  int
    height: int
    label:  str = ""

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height,
            "label": self.label,
            "center": list(self.center),
        }


# ─────────────────────────────────────────────────────────────────────────────
# ControlResult — aggregated result of a ControlManager.execute() call
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ControlResult:
    session_id:  str
    goal:        str
    actions:     List[ControlAction] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for a in self.actions if a.status == ActionStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for a in self.actions if a.status == ActionStatus.FAILED)

    @property
    def denied_count(self) -> int:
        return sum(1 for a in self.actions if a.status == ActionStatus.DENIED)

    @property
    def all_succeeded(self) -> bool:
        return self.failed_count == 0 and self.success_count > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id":    self.session_id,
            "goal":          self.goal,
            "success_count": self.success_count,
            "failed_count":  self.failed_count,
            "denied_count":  self.denied_count,
            "actions":       [a.to_dict() for a in self.actions],
        }
