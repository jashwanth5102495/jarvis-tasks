"""
terminal_executor.py
====================
TerminalExecutor — controlled shell command execution.

Safety model
------------
- SAFE_COMMANDS whitelist: only commands whose first token appears in the
  whitelist are allowed through run_safe_command.
- BLOCKED_PATTERNS: substring patterns that are always rejected regardless
  of whitelist status.
- All commands run with a configurable timeout (default 30 s).
- stdout + stderr are captured and returned as a single string.
- The working directory is always the sandbox workspace root.

Supported actions
-----------------
run_safe_command   : run a whitelisted shell command
run_python_script  : execute a Python script inside the workspace
check_python       : verify Python is available (python --version)
install_package    : pip install <package> (HIGH risk, requires approval)
run_tests          : run pytest inside the workspace
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path
from typing import List

from jarvis.execution.execution_context import ExecutionContext, RiskLevel
from jarvis.execution.sandbox import sandbox
from jarvis.skills.base import BaseExecutor

logger = logging.getLogger(__name__)

# ── Safety configuration ───────────────────────────────────────────────────────

SAFE_COMMANDS: set[str] = {
    "python", "python3", "pip", "pip3",
    "pytest", "py.test",
    "dir", "ls", "echo",
    "type", "cat",
    "mkdir", "md",
    "node", "npm", "npx",
    "git",
    "curl",
}

BLOCKED_PATTERNS: list[str] = [
    "rm -rf", "rmdir /s", "del /f", "del /s",
    "format ", "shutdown", "reboot", "halt",
    ":(){:|:&};:", "mkfs", "dd if=",
    "chmod 777 /", "sudo rm", "sudo shutdown",
    "reg delete", "reg add HKLM",
    "taskkill /f /im",
    "> /dev/", "| bash", "| sh",
    "wget http", "curl http",   # allow https only
]

DEFAULT_TIMEOUT = 30   # seconds


class TerminalExecutor(BaseExecutor):

    SUPPORTED_ACTIONS = [
        "run_safe_command",
        "run_python_script",
        "check_python",
        "install_package",
        "run_tests",
    ]

    ACTION_RISK_MAP = {
        "run_safe_command":  RiskLevel.MEDIUM,
        "run_python_script": RiskLevel.MEDIUM,
        "check_python":      RiskLevel.SAFE,
        "install_package":   RiskLevel.HIGH,
        "run_tests":         RiskLevel.MEDIUM,
    }

    # ── Action handlers ────────────────────────────────────────────────────────

    def _action_run_safe_command(self, ctx: ExecutionContext) -> str:
        command = ctx.params.get("command", "")
        timeout = ctx.params.get("timeout", DEFAULT_TIMEOUT)
        self._validate_command(command)
        return self._run(command, timeout=timeout)

    def _action_run_python_script(self, ctx: ExecutionContext) -> str:
        script_path = ctx.params["script_path"]
        safe_path   = sandbox.resolve(script_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        command = f"python {safe_path}"
        return self._run(command, timeout=ctx.params.get("timeout", DEFAULT_TIMEOUT))

    def _action_check_python(self, ctx: ExecutionContext) -> str:
        return self._run("python --version", timeout=10)

    def _action_install_package(self, ctx: ExecutionContext) -> str:
        package = ctx.params.get("package", "")
        if not package or not self._is_safe_package_name(package):
            raise ValueError(f"Invalid or unsafe package name: {package!r}")
        command = f"pip install {package}"
        return self._run(command, timeout=120)

    def _action_run_tests(self, ctx: ExecutionContext) -> str:
        test_path = ctx.params.get("test_path", ".")
        safe_path = sandbox.resolve(test_path)
        command   = f"pytest {safe_path} -v --tb=short"
        return self._run(command, timeout=120)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _run(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        logger.info(f"TerminalExecutor: running {command!r}")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(sandbox.root),
            )
            output = (result.stdout + result.stderr).strip()
            if result.returncode != 0:
                raise RuntimeError(
                    f"Command exited with code {result.returncode}.\n{output}"
                )
            logger.info(f"TerminalExecutor: success, output={output[:200]!r}")
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out after {timeout}s: {command!r}")

    @staticmethod
    def _validate_command(command: str) -> None:
        """Raise ValueError if command is blocked or not whitelisted."""
        cmd_lower = command.lower().strip()

        # Check blocked patterns first
        for pattern in BLOCKED_PATTERNS:
            if pattern in cmd_lower:
                raise ValueError(
                    f"Command blocked — matches unsafe pattern {pattern!r}: {command!r}"
                )

        # Check whitelist (first token)
        try:
            first_token = shlex.split(command)[0].lower()
        except ValueError:
            raise ValueError(f"Malformed command: {command!r}")

        # Strip path prefix (e.g. /usr/bin/python → python)
        first_token = Path(first_token).name

        if first_token not in SAFE_COMMANDS:
            raise ValueError(
                f"Command not in safe whitelist: {first_token!r}. "
                f"Allowed: {sorted(SAFE_COMMANDS)}"
            )

    @staticmethod
    def _is_safe_package_name(name: str) -> bool:
        """Basic package name validation — alphanumeric, hyphens, underscores only."""
        import re
        return bool(re.fullmatch(r"[a-zA-Z0-9_\-\.\[\]>=<!, ]+", name))
