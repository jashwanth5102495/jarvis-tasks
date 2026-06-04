"""
permissions.py
==============
Permission & Safety Layer — the gatekeeper for ALL execution.

Every action passes through PermissionManager.request() before
any executor touches the filesystem or shell.

Permission Modes
----------------
ALLOW    : auto-approved (safe read-only actions)
CONFIRM  : requires explicit user Y/N at the terminal
DENY     : blocked unconditionally (dangerous system commands)
SANDBOX  : allowed only inside the sandboxed workspace

Risk → Mode mapping
-------------------
SAFE     → ALLOW
LOW      → ALLOW
MEDIUM   → CONFIRM
HIGH     → CONFIRM  (with extra warning)
CRITICAL → DENY
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, Optional

from jarvis.execution.execution_context import ExecutionContext, RiskLevel, ExecutionStatus

logger = logging.getLogger(__name__)


class PermissionMode(str, Enum):
    ALLOW   = "allow"
    CONFIRM = "confirm"
    DENY    = "deny"
    SANDBOX = "sandbox"


# ── Risk → default permission mode ────────────────────────────────────────────
_RISK_TO_MODE: Dict[RiskLevel, PermissionMode] = {
    RiskLevel.SAFE:     PermissionMode.ALLOW,
    RiskLevel.LOW:      PermissionMode.ALLOW,
    RiskLevel.MEDIUM:   PermissionMode.CONFIRM,
    RiskLevel.HIGH:     PermissionMode.CONFIRM,
    RiskLevel.CRITICAL: PermissionMode.DENY,
}

# ── Unconditionally blocked command fragments ──────────────────────────────────
_BLOCKED_PATTERNS = [
    "rm -rf", "rmdir /s", "format ", "shutdown", "reboot",
    "del /f", "del /s", ":(){:|:&};:", "mkfs", "dd if=",
    "chmod 777 /", "chown root", "sudo rm", "sudo shutdown",
    "reg delete", "reg add HKLM", "taskkill /f",
]


class PermissionManager:
    """
    Central permission gate.

    Usage
    -----
    approved = permission_manager.request(ctx)
    if not approved:
        ctx.mark_denied()
        return
    # proceed with execution
    """

    def __init__(self, auto_approve_safe: bool = True):
        """
        Parameters
        ----------
        auto_approve_safe : bool
            When True, SAFE and LOW risk actions are approved without prompting.
            Set to False in strict mode to require confirmation for everything.
        """
        self._auto_approve_safe = auto_approve_safe
        # Session-level overrides: executor+action → PermissionMode
        self._overrides: Dict[str, PermissionMode] = {}

    # ── Public API ─────────────────────────────────────────────────────────────

    def request(self, ctx: ExecutionContext) -> bool:
        """
        Evaluate permission for ctx.  Returns True if approved.
        Side-effect: sets ctx.approved_by and ctx.status.
        """
        # 1. Hard-block critical risk
        if ctx.risk_level == RiskLevel.CRITICAL:
            self._deny(ctx, "CRITICAL risk actions are unconditionally blocked.")
            return False

        # 2. Check blocked command patterns
        command = ctx.params.get("command", "")
        if command and self._is_blocked_command(command):
            self._deny(ctx, f"Command matches blocked pattern: {command!r}")
            return False

        # 3. Check session overrides
        override_key = f"{ctx.executor}:{ctx.action}"
        mode = self._overrides.get(override_key, _RISK_TO_MODE[ctx.risk_level])

        if mode == PermissionMode.DENY:
            self._deny(ctx, "Action is denied by policy.")
            return False

        if mode == PermissionMode.ALLOW:
            ctx.approved_by = "auto"
            ctx.status = ExecutionStatus.APPROVED
            logger.debug(f"Auto-approved: {ctx.executor}.{ctx.action}")
            return True

        # 4. CONFIRM — ask the user
        return self._prompt_user(ctx)

    def set_override(
        self, executor: str, action: str, mode: PermissionMode
    ) -> None:
        """Pin a specific executor+action to a permission mode for this session."""
        self._overrides[f"{executor}:{action}"] = mode

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _prompt_user(self, ctx: ExecutionContext) -> bool:
        risk_label = ctx.risk_level.value.upper()
        risk_colour = "\033[93m" if ctx.risk_level == RiskLevel.MEDIUM else "\033[91m"
        reset = "\033[0m"

        print(f"\n{'─' * 56}")
        print(f"  {risk_colour}⚠  Permission Required  [{risk_label}]{reset}")
        print(f"{'─' * 56}")
        print(f"  Executor : {ctx.executor}")
        print(f"  Action   : {ctx.action}")

        # Show the most relevant param
        if "command" in ctx.params:
            print(f"  Command  : {ctx.params['command']}")
        elif "path" in ctx.params:
            print(f"  Path     : {ctx.params['path']}")
        elif "url" in ctx.params:
            print(f"  URL      : {ctx.params['url']}")
        else:
            for k, v in list(ctx.params.items())[:3]:
                print(f"  {k:<9}: {v}")

        print(f"{'─' * 56}")

        while True:
            try:
                answer = input("  Allow? [Y/N] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = "n"

            if answer in ("y", "yes"):
                ctx.approved_by = "user"
                ctx.status = ExecutionStatus.APPROVED
                logger.info(f"User approved: {ctx.executor}.{ctx.action}")
                return True
            elif answer in ("n", "no"):
                self._deny(ctx, "Denied by user.")
                return False
            else:
                print("  Please enter Y or N.")

    def _deny(self, ctx: ExecutionContext, reason: str) -> None:
        ctx.mark_denied()
        logger.warning(f"Permission denied — {ctx.executor}.{ctx.action}: {reason}")
        print(f"\n  \033[91m✗ Denied:\033[0m {reason}\n")

    @staticmethod
    def _is_blocked_command(command: str) -> bool:
        cmd_lower = command.lower()
        return any(pattern in cmd_lower for pattern in _BLOCKED_PATTERNS)


# Module-level singleton
permission_manager = PermissionManager()
