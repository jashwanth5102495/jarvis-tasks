"""
workflow_memory.py
==================
Persistent workflow memory — stores completed WorkflowState objects to:
  1. JSONL log file  (logs/workflow_logs/YYYY-MM-DD.jsonl)
  2. MongoDB collection "workflow_logs"  (best-effort)

Also maintains an in-memory index for fast querying within a session.
"""

from __future__ import annotations

import json
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque, List, Optional

from orchestration.workflow_state import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)

_LOG_DIR     = Path(__file__).parent.parent / "logs" / "workflow_logs"
_BUFFER_SIZE = 200


class WorkflowMemory:
    """
    Append-only workflow history store.

    Usage
    -----
    workflow_memory.save(state)
    recent = workflow_memory.get_recent(10)
    failed = workflow_memory.get_failed()
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        buffer_size: int = _BUFFER_SIZE,
    ):
        self._log_dir = Path(log_dir or _LOG_DIR)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: Deque[WorkflowState] = deque(maxlen=buffer_size)

    # ── Public API ─────────────────────────────────────────────────────────────

    def save(self, state: WorkflowState) -> None:
        self._buffer.append(state)
        self._write_file(state)
        self._write_mongo(state)

    def get_recent(self, n: int = 10) -> List[WorkflowState]:
        items = list(self._buffer)
        return list(reversed(items))[:n]

    def get_by_id(self, workflow_id: str) -> Optional[WorkflowState]:
        for s in self._buffer:
            if s.workflow_id == workflow_id:
                return s
        return None

    def get_by_name(self, name: str) -> List[WorkflowState]:
        return [s for s in self._buffer if s.workflow_name == name]

    def get_failed(self) -> List[WorkflowState]:
        return [
            s for s in self._buffer
            if s.status in (WorkflowStatus.FAILED, WorkflowStatus.PARTIALLY_COMPLETED)
        ]

    def get_completed(self) -> List[WorkflowState]:
        return [s for s in self._buffer if s.status == WorkflowStatus.COMPLETED]

    def summary(self) -> dict:
        all_items = list(self._buffer)
        return {
            "total":     len(all_items),
            "completed": sum(1 for s in all_items if s.status == WorkflowStatus.COMPLETED),
            "partial":   sum(1 for s in all_items if s.status == WorkflowStatus.PARTIALLY_COMPLETED),
            "failed":    sum(1 for s in all_items if s.status == WorkflowStatus.FAILED),
            "cancelled": sum(1 for s in all_items if s.status == WorkflowStatus.CANCELLED),
        }

    # ── Internal ───────────────────────────────────────────────────────────────

    def _write_file(self, state: WorkflowState) -> None:
        try:
            date_str  = datetime.now().strftime("%Y-%m-%d")
            log_file  = self._log_dir / f"{date_str}.jsonl"
            line      = json.dumps(state.to_dict(), ensure_ascii=False, default=str)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:
            logger.warning(f"WorkflowMemory file write failed: {exc}")

    def _write_mongo(self, state: WorkflowState) -> None:
        try:
            from database.mongodb import mongodb
            mongodb.insert_one("workflow_logs", state.to_dict())
        except Exception as exc:
            logger.debug(f"WorkflowMemory MongoDB write skipped: {exc}")


# Module-level singleton
workflow_memory = WorkflowMemory()
