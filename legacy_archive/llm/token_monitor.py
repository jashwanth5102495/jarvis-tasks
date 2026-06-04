
"""
token_monitor.py
================
Monitors and manages token usage for LLMs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Record of token usage for a single request."""
    model: str
    prompt_tokens: int
    completion_tokens: int
    timestamp: datetime


class TokenMonitor:
    """
    Tracks and manages token usage for LLM operations.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self._log_dir = log_dir or Path(__file__).parent.parent / "logs" / "llm_logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._usage: Dict[str, int] = {}  # model -> total tokens
        self._daily_usage: Dict[str, int] = {}  # date -> total tokens
        self._daily_limit: Optional[int] = None

    def set_daily_limit(self, limit: int) -> None:
        """Set a daily token usage limit."""
        self._daily_limit = limit
        logger.info(f"Set daily token limit: {limit}")

    def get_usage_for_model(self, model: str) -> int:
        """Get total token usage for a specific model."""
        return self._usage.get(model, 0)

    def get_daily_usage(self) -> int:
        """Get token usage for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self._daily_usage.get(today, 0)

    def record_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage for a request."""
        total = prompt_tokens + completion_tokens
        self._usage[model] = self._usage.get(model, 0) + total

        today = datetime.now().strftime("%Y-%m-%d")
        self._daily_usage[today] = self._daily_usage.get(today, 0) + total

        logger.info(
            f"Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total} total for model {model}"
        )

    def check_limit(self) -> bool:
        """Check if we're within the daily limit (if set)."""
        if self._daily_limit is None:
            return True
        return self.get_daily_usage() < self._daily_limit


# Module-level singleton
token_monitor = TokenMonitor()

