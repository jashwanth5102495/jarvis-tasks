
"""
semantic_action_registry.py
===========================
Centralized semantic action registry for JARVIS AI OS.
Maps semantic action names to executors, handlers, and fallbacks.
"""

import logging
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SemanticActionEntry:
    name: str
    executor: str
    action: str
    handler: Optional[Callable]
    fallback: Optional[Callable] = None
    description: str = ""


class SemanticActionRegistry:
    def __init__(self):
        self._actions: Dict[str, SemanticActionEntry] = {}
        logger.info("Semantic Action Registry initialized")

    def register(self, entry: SemanticActionEntry):
        self._actions[entry.name.lower()] = entry
        logger.debug(f"Registered semantic action: {entry.name}")

    def get(self, name: str) -> Optional[SemanticActionEntry]:
        return self._actions.get(name.lower())

    def list_actions(self):
        return list(self._actions.keys())


# Module-level singleton
semantic_action_registry = SemanticActionRegistry()
