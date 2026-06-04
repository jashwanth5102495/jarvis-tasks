"""
file_executor.py
================
FileExecutor — safe, sandboxed file system operations.

Supported actions
-----------------
create_file   : create a new file (and parent dirs) with optional content
read_file     : read and return file content
write_file    : overwrite a file with new content
append_file   : append content to an existing file (creates if missing)
delete_file   : delete a file (requires MEDIUM risk approval)
list_dir      : list files in a directory
create_dir    : create a directory tree
rename_file   : rename / move a file within the workspace

All paths are validated through the Sandbox before any I/O.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from skills.execution.execution_context import ExecutionContext, RiskLevel
from skills.execution.sandbox import sandbox, SandboxViolation
from skills.executors.base_executor import BaseExecutor

logger = logging.getLogger(__name__)


class FileExecutor(BaseExecutor):

    SUPPORTED_ACTIONS = [
        "create_file",
        "read_file",
        "write_file",
        "append_file",
        "delete_file",
        "list_dir",
        "create_dir",
        "rename_file",
    ]

    ACTION_RISK_MAP = {
        "create_file":  RiskLevel.LOW,
        "read_file":    RiskLevel.SAFE,
        "write_file":   RiskLevel.LOW,
        "append_file":  RiskLevel.LOW,
        "delete_file":  RiskLevel.MEDIUM,
        "list_dir":     RiskLevel.SAFE,
        "create_dir":   RiskLevel.LOW,
        "rename_file":  RiskLevel.LOW,
    }

    # ── Action handlers ────────────────────────────────────────────────────────

    def _action_create_file(self, ctx: ExecutionContext) -> str:
        path    = ctx.params["path"]
        content = ctx.params.get("content", "")
        target  = sandbox.resolve(path)

        if target.exists():
            return f"File already exists: {sandbox.relative_display(target)}"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info(f"FileExecutor: created {target}")
        return f"Created: {sandbox.relative_display(target)}"

    def _action_read_file(self, ctx: ExecutionContext) -> str:
        path   = ctx.params["path"]
        target = sandbox.resolve(path)

        if not target.exists():
            raise FileNotFoundError(f"File not found: {sandbox.relative_display(target)}")

        content = target.read_text(encoding="utf-8")
        logger.info(f"FileExecutor: read {target} ({len(content)} chars)")
        return content

    def _action_write_file(self, ctx: ExecutionContext) -> str:
        path    = ctx.params["path"]
        content = ctx.params.get("content", "")
        target  = sandbox.resolve(path)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info(f"FileExecutor: wrote {target}")
        return f"Written: {sandbox.relative_display(target)}"

    def _action_append_file(self, ctx: ExecutionContext) -> str:
        path    = ctx.params["path"]
        content = ctx.params.get("content", "")
        target  = sandbox.resolve(path)

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"FileExecutor: appended to {target}")
        return f"Appended to: {sandbox.relative_display(target)}"

    def _action_delete_file(self, ctx: ExecutionContext) -> str:
        path   = ctx.params["path"]
        target = sandbox.resolve(path)

        if not target.exists():
            return f"File not found (nothing deleted): {sandbox.relative_display(target)}"

        if target.is_dir():
            shutil.rmtree(target)
            logger.info(f"FileExecutor: deleted directory {target}")
            return f"Deleted directory: {sandbox.relative_display(target)}"
        else:
            target.unlink()
            logger.info(f"FileExecutor: deleted file {target}")
            return f"Deleted: {sandbox.relative_display(target)}"

    def _action_list_dir(self, ctx: ExecutionContext) -> str:
        path   = ctx.params.get("path", ".")
        target = sandbox.resolve(path)

        if not target.exists():
            return f"Directory not found: {sandbox.relative_display(target)}"

        entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
        lines   = []
        for entry in entries:
            prefix = "📁 " if entry.is_dir() else "📄 "
            lines.append(f"  {prefix}{entry.name}")

        result = "\n".join(lines) if lines else "  (empty)"
        logger.info(f"FileExecutor: listed {target} ({len(entries)} entries)")
        return result

    def _action_create_dir(self, ctx: ExecutionContext) -> str:
        path   = ctx.params["path"]
        target = sandbox.resolve(path)
        target.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileExecutor: created directory {target}")
        return f"Directory created: {sandbox.relative_display(target)}"

    def _action_rename_file(self, ctx: ExecutionContext) -> str:
        src_path  = ctx.params["path"]
        dest_path = ctx.params["new_path"]
        src       = sandbox.resolve(src_path)
        dest      = sandbox.resolve(dest_path)

        if not src.exists():
            raise FileNotFoundError(f"Source not found: {sandbox.relative_display(src)}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dest)
        logger.info(f"FileExecutor: renamed {src} → {dest}")
        return (
            f"Renamed: {sandbox.relative_display(src)} "
            f"→ {sandbox.relative_display(dest)}"
        )
