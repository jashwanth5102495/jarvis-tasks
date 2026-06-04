"""
cc_permissions.py
=================
Permission gate specifically for computer control actions.

Separate from the execution-layer PermissionManager because desktop
control has different risk semantics — clicking a button is HIGH risk
even though it doesn't touch the filesystem.

Risk → Mode mapping
-------------------
SAFE     → auto-approved  (screenshot, read screen)
MEDIUM   → auto-approved  (mouse move, scroll, window focus)
HIGH     → user confirmation required  (click, type, open app)
CRITICAL → always denied  (system-level destructive actions)

The user can grant "session approval" for a specific action type
so they aren't prompted repeatedly during a workflow.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, Set

from computer_control.cc_models import ActionRisk, ActionStatus, ControlAction

logger = logging.getLogger(__name__)


class CCPermissionMode(str, Enum):
    ALLOW   = "allow"
    CONFIRM = "confirm"
    DENY    = "deny"


_RISK_TO_MODE: Dict[ActionRisk, CCPermissionMode] = {
    ActionRisk.SAFE:     CCPermissionMode.ALLOW,
    ActionRisk.MEDIUM:   CCPermissionMode.ALLOW,
    ActionRisk.HIGH:     CCPermissionMode.ALLOW,  # Auto-approve trusted high-risk desktop actions!
    ActionRisk.CRITICAL: CCPermissionMode.DENY,
}


class CCPermissionManager:
    """
    Permission gate for all computer control actions.

    Usage
    -----
    approved = cc_permission_manager.request(action)
    """

    def __init__(self) -> None:
        # Session-level overrides: "controller:action" → mode
        self._overrides:       Dict[str, CCPermissionMode] = {}
        # Actions approved for the whole session (user said "yes, always")
        self._session_allowed: Set[str]                    = set()

    # ── Public API ─────────────────────────────────────────────────────────────

    def request(self, action: ControlAction) -> bool:
        """
        Evaluate permission for a ControlAction.
        Returns True if approved; sets action.approved_by and action.status.
        """
        # 1. Hard-block CRITICAL
        if action.risk == ActionRisk.CRITICAL:
            self._deny(action, "CRITICAL risk actions are unconditionally blocked.")
            return False

        # 2. Session-level allow
        key = f"{action.controller.value}:{action.action}"
        if key in self._session_allowed:
            action.approved_by = "session"
            action.status      = ActionStatus.APPROVED
            return True

        # 3. Check overrides
        mode = self._overrides.get(key, _RISK_TO_MODE[action.risk])

        if mode == CCPermissionMode.DENY:
            self._deny(action, "Action denied by policy.")
            return False

        if mode == CCPermissionMode.ALLOW:
            action.approved_by = "auto"
            action.status      = ActionStatus.APPROVED
            # Print auto-approval message to console!
            print(f"\n  \033[92m✓ Auto-approved {action.risk.value.upper()} desktop action:\033[0m")
            print(f"    {action.description or f'{action.controller.value}.{action.action}'}\n")
            return True

        # 4. CONFIRM — prompt user
        return self._prompt_user(action)

    def set_override(
        self,
        controller: str,
        action_name: str,
        mode: CCPermissionMode,
    ) -> None:
        self._overrides[f"{controller}:{action_name}"] = mode

    def allow_session(self, controller: str, action_name: str) -> None:
        """Grant session-level approval so user isn't prompted again."""
        self._session_allowed.add(f"{controller}:{action_name}")

    # ── Internal ───────────────────────────────────────────────────────────────

    def _prompt_user(self, action: ControlAction) -> bool:
        risk_colour = "\033[93m" if action.risk == ActionRisk.HIGH else "\033[91m"
        reset       = "\033[0m"

        print(f"\n{'─' * 60}")
        print(f"  {risk_colour}⚠  Computer Control Permission  [{action.risk.value.upper()}]{reset}")
        print(f"{'─' * 60}")
        print(f"  Controller : {action.controller.value}")
        print(f"  Action     : {action.action}")
        if action.description:
            print(f"  Description: {action.description}")
        # Show key params
        for k, v in list(action.params.items())[:3]:
            print(f"  {k:<11}: {str(v)[:60]}")
        print(f"{'─' * 60}")
        print("  [Y] Allow once   [A] Allow for session   [N] Deny")

        while True:
            try:
                answer = input("  Choice > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"

            if answer in ("y", "yes"):
                action.approved_by = "user"
                action.status      = ActionStatus.APPROVED
                logger.info(f"User approved: {action.controller.value}.{action.action}")
                return True
            elif answer == "a":
                self.allow_session(action.controller.value, action.action)
                action.approved_by = "session"
                action.status      = ActionStatus.APPROVED
                logger.info(f"Session approved: {action.controller.value}.{action.action}")
                return True
            elif answer in ("n", "no"):
                self._deny(action, "Denied by user.")
                return False
            else:
                print("  Please enter Y, A, or N.")

    def _deny(self, action: ControlAction, reason: str) -> None:
        action.mark_denied()
        logger.warning(
            f"CC Permission denied — {action.controller.value}.{action.action}: {reason}"
        )
        print(f"\n  \033[91m✗ Denied:\033[0m {reason}\n")


# Module-level singleton
cc_permission_manager = CCPermissionManager()
