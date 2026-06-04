"""
base_executor.py
================
Abstract base class for all JARVIS executors.

Every executor must:
  1. Inherit from BaseExecutor
  2. Implement execute(ctx) → str
  3. Declare its supported actions in SUPPORTED_ACTIONS
  4. Declare the risk level for each action in ACTION_RISK_MAP

The base class provides:
  - Action dispatch via execute()
  - Automatic unsupported-action error
  - Sandbox path resolution helper
  - Structured logging
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from jarvis.execution.execution_context import ExecutionContext, RiskLevel
from jarvis.execution.sandbox import sandbox

logger = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """Abstract base for all JARVIS executors."""

    # Subclasses declare which actions they handle
    SUPPORTED_ACTIONS: list[str] = []

    # Subclasses declare the risk level for each action
    ACTION_RISK_MAP: Dict[str, RiskLevel] = {}

    @property
    def name(self) -> str:
        return self.__class__.__name__.replace("Executor", "").lower()

    def execute(self, ctx: ExecutionContext) -> str:
        """
        Dispatch to the appropriate handler method.
        Handler methods are named  _action_<action_name>(ctx) → str.
        """
        if ctx.action not in self.SUPPORTED_ACTIONS:
            raise ValueError(
                f"{self.__class__.__name__} does not support action {ctx.action!r}. "
                f"Supported: {self.SUPPORTED_ACTIONS}"
            )

        handler_name = f"_action_{ctx.action}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} is missing handler {handler_name!r}"
            )

        logger.info(f"[{self.name}] executing action={ctx.action!r} params={ctx.params}")
        return handler(ctx)

    def risk_for(self, action: str) -> RiskLevel:
        return self.ACTION_RISK_MAP.get(action, RiskLevel.MEDIUM)

    # ── Sandbox helper ─────────────────────────────────────────────────────────

    @staticmethod
    def safe_path(relative: str):
        """Resolve a relative path inside the sandbox workspace."""
        return sandbox.resolve(relative)
