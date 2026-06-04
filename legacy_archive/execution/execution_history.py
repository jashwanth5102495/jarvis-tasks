"""
execution_history.py
====================
Persistent execution history — writes every ExecutionContext to:
  1. A rotating JSON-lines log file  (logs/execution_logs/YYYY-MM-DD.jsonl)
  2. MongoDB collection "execution_logs"  (best-effort, never crashes the system)

The in-memory buffer lets the rest of the system query recent history
without hitting the database.
"""

from __future__ import annotations

import json
import logging
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional

from skills.execution.execution_context import ExecutionContext, ExecutionStatus

logger = logging.getLogger(__name__)

_LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "execution_logs"
_BUFFER_SIZE = 500   # keep last N contexts in memory


class ExecutionHistory:
    """
    Append-only execution log with in-memory buffer + file persistence.

    Usage
    -----
    history.record(ctx)
    recent = history.get_recent(20)
    failed = history.get_failed()
    """

    def __init__(self, log_dir: Optional[Path] = None, buffer_size: int = _BUFFER_SIZE):
        self._log_dir = Path(log_dir or _LOG_DIR)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: Deque[ExecutionContext] = deque(maxlen=buffer_size)

    # ── Public API ─────────────────────────────────────────────────────────────

    def record(self, ctx: ExecutionContext) -> None:
        """Persist a completed ExecutionContext."""
        self._buffer.append(ctx)
        self._write_file(ctx)
        self._write_mongo(ctx)

    def get_recent(self, n: int = 20) -> List[ExecutionContext]:
        """Return the N most recent contexts (newest first)."""
        items = list(self._buffer)
        return list(reversed(items))[:n]

    def get_by_task(self, task_id: str) -> List[ExecutionContext]:
        return [c for c in self._buffer if c.task_id == task_id]

    def get_failed(self) -> List[ExecutionContext]:
        return [c for c in self._buffer if c.status == ExecutionStatus.FAILED]

    def get_by_executor(self, executor: str) -> List[ExecutionContext]:
        return [c for c in self._buffer if c.executor == executor]

    def summary(self) -> dict:
        all_items = list(self._buffer)
        return {
            "total":    len(all_items),
            "success":  sum(1 for c in all_items if c.status == ExecutionStatus.SUCCESS),
            "failed":   sum(1 for c in all_items if c.status == ExecutionStatus.FAILED),
            "denied":   sum(1 for c in all_items if c.status == ExecutionStatus.DENIED),
            "skipped":  sum(1 for c in all_items if c.status == ExecutionStatus.SKIPPED),
        }

    # ── Internal ───────────────────────────────────────────────────────────────

    def _write_file(self, ctx: ExecutionContext) -> None:
        try:
            date_str  = datetime.now().strftime("%Y-%m-%d")
            log_file  = self._log_dir / f"{date_str}.jsonl"
            line      = json.dumps(ctx.to_dict(), ensure_ascii=False)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:
            logger.warning(f"ExecutionHistory file write failed: {exc}")

    def _write_mongo(self, ctx: ExecutionContext) -> None:
        try:
            from database.mongodb import mongodb
            mongodb.insert_one("execution_logs", ctx.to_dict())
        except Exception as exc:
            # MongoDB is optional — never crash the execution pipeline
            logger.debug(f"ExecutionHistory MongoDB write skipped: {exc}")


# Module-level singleton
execution_history = ExecutionHistory()
