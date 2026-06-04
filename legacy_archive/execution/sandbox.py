"""
sandbox.py
==========
Sandbox environment — enforces that ALL file operations stay inside
the designated workspace directory.

Rules
-----
- Every path passed to an executor is resolved and validated here.
- Paths that escape the workspace root are rejected with SandboxViolation.
- The workspace directory is created on first use if it doesn't exist.
- Symlink traversal is detected and blocked.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default workspace root — sits next to the project root
_DEFAULT_WORKSPACE = (
    Path(__file__).parent.parent.parent / "workspace"
)


class SandboxViolation(Exception):
    """Raised when a path escapes the sandbox boundary."""


class Sandbox:
    """
    Validates and resolves paths relative to the workspace root.

    Usage
    -----
    safe_path = sandbox.resolve("project/app.py")
    # → Path("…/workspace/project/app.py")

    sandbox.validate(some_path)   # raises SandboxViolation if outside
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self._root = Path(workspace_root or _DEFAULT_WORKSPACE).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Sandbox workspace: {self._root}")

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def root(self) -> Path:
        return self._root

    def resolve(self, relative_path: str | Path) -> Path:
        """
        Resolve a relative path inside the workspace.
        Raises SandboxViolation if the resolved path escapes the root.
        """
        candidate = (self._root / relative_path).resolve()
        self._check(candidate)
        return candidate

    def validate(self, path: str | Path) -> Path:
        """
        Validate an absolute path is inside the workspace.
        Returns the resolved Path on success.
        """
        resolved = Path(path).resolve()
        self._check(resolved)
        return resolved

    def relative_display(self, path: Path) -> str:
        """Return a workspace-relative display string, e.g. 'project/app.py'."""
        try:
            return str(path.relative_to(self._root))
        except ValueError:
            return str(path)

    def ensure_dir(self, relative_path: str | Path) -> Path:
        """Create a directory inside the workspace and return its path."""
        target = self.resolve(relative_path)
        target.mkdir(parents=True, exist_ok=True)
        return target

    # ── Internal ───────────────────────────────────────────────────────────────

    def _check(self, resolved: Path) -> None:
        # Detect symlink escape
        try:
            resolved.relative_to(self._root)
        except ValueError:
            raise SandboxViolation(
                f"Path escapes sandbox boundary.\n"
                f"  Attempted : {resolved}\n"
                f"  Workspace : {self._root}"
            )


# Module-level singleton
sandbox = Sandbox()
