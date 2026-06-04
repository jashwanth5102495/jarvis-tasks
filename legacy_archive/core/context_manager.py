"""
context_manager.py
==================
SharedContext — the single source of truth that all executors
read from and write to during a workflow run.

Every executor action can:
  - Read prior outputs  (e.g. browser results, generated file paths)
  - Write its own outputs  (e.g. created files, installed packages)
  - Pass data to downstream steps via the context

This is the backbone of cross-executor communication.

Structure
---------
{
  "workflow_id":        str,
  "task_id":            str,
  "goal":               str,
  "category":           str,

  # Artifact registries (written by executors)
  "generated_files":    [str, ...],
  "created_dirs":       [str, ...],
  "installed_packages": [str, ...],
  "browser_results":    [{"url": str, "snippet": str}, ...],
  "execution_outputs":  [{"step": str, "output": str}, ...],
  "errors":             [{"step": str, "error": str}, ...],

  # Cross-executor messaging
  "messages":           [{"from": str, "to": str, "key": str, "value": Any}, ...],

  # Arbitrary key-value store for executor-to-executor data passing
  "store":              {str: Any},
}
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SharedContext:
    """
    Mutable shared state for one workflow execution.

    All executors receive a reference to the same SharedContext instance.
    Thread-safety is not required for Milestone 3 (sequential execution).
    The architecture is designed to add locking in future parallel execution.

    Usage
    -----
    ctx.add_file("project/app.py")
    ctx.add_package("flask")
    ctx.set("project_name", "my_api")
    name = ctx.get("project_name")
    ctx.post_message(from_="browser", to="coding", key="template_url", value="...")
    """

    def __init__(
        self,
        workflow_id: str,
        task_id: str,
        goal: str,
        category: str,
    ):
        self.workflow_id:        str                    = workflow_id
        self.task_id:            str                    = task_id
        self.goal:               str                    = goal
        self.category:           str                    = category
        self.created_at:         datetime               = datetime.now()

        # ── Artifact registries ───────────────────────────────────────────────
        self.generated_files:    List[str]              = []
        self.created_dirs:       List[str]              = []
        self.installed_packages: List[str]              = []
        self.browser_results:    List[Dict[str, str]]   = []
        self.execution_outputs:  List[Dict[str, str]]   = []
        self.errors:             List[Dict[str, str]]   = []

        # ── Cross-executor messaging ──────────────────────────────────────────
        self.messages:           List[Dict[str, Any]]   = []

        # ── Arbitrary key-value store ─────────────────────────────────────────
        self._store:             Dict[str, Any]         = {}

    # ── Artifact writers ──────────────────────────────────────────────────────

    def add_file(self, path: str) -> None:
        if path not in self.generated_files:
            self.generated_files.append(path)
            logger.debug(f"SharedContext: file registered → {path}")

    def add_dir(self, path: str) -> None:
        if path not in self.created_dirs:
            self.created_dirs.append(path)

    def add_package(self, package: str) -> None:
        if package not in self.installed_packages:
            self.installed_packages.append(package)

    def add_browser_result(self, url: str, snippet: str) -> None:
        self.browser_results.append({"url": url, "snippet": snippet[:500]})

    def add_output(self, step_name: str, output: str) -> None:
        self.execution_outputs.append({"step": step_name, "output": output[:1000]})

    def add_error(self, step_name: str, error: str) -> None:
        self.errors.append({"step": step_name, "error": error})

    # ── Key-value store ───────────────────────────────────────────────────────

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
        logger.debug(f"SharedContext: store[{key!r}] = {str(value)[:80]}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._store

    # ── Cross-executor messaging ──────────────────────────────────────────────

    def post_message(
        self,
        from_executor: str,
        to_executor: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Send a typed message from one executor to another.
        The receiving executor reads it via read_messages().
        """
        msg = {
            "from":      from_executor,
            "to":        to_executor,
            "key":       key,
            "value":     value,
            "timestamp": datetime.now().isoformat(),
        }
        self.messages.append(msg)
        logger.debug(
            f"SharedContext: message {from_executor!r} → {to_executor!r} "
            f"key={key!r}"
        )

    def read_messages(
        self,
        to_executor: str,
        key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return all messages addressed to `to_executor`, optionally filtered by key."""
        msgs = [m for m in self.messages if m["to"] == to_executor]
        if key:
            msgs = [m for m in msgs if m["key"] == key]
        return msgs

    def get_message_value(
        self,
        to_executor: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Convenience: get the value of the latest message matching to+key."""
        msgs = self.read_messages(to_executor, key)
        return msgs[-1]["value"] if msgs else default

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id":        self.workflow_id,
            "task_id":            self.task_id,
            "goal":               self.goal,
            "category":           self.category,
            "created_at":         self.created_at.isoformat(),
            "generated_files":    self.generated_files,
            "created_dirs":       self.created_dirs,
            "installed_packages": self.installed_packages,
            "browser_results":    self.browser_results,
            "execution_outputs":  self.execution_outputs,
            "errors":             self.errors,
            "messages":           self.messages,
            "store":              {
                k: str(v)[:200] for k, v in self._store.items()
            },
        }

    def __repr__(self) -> str:
        return (
            f"SharedContext(workflow={self.workflow_id!r}, "
            f"files={len(self.generated_files)}, "
            f"packages={len(self.installed_packages)}, "
            f"errors={len(self.errors)})"
        )
