
"""
semantic_runtime
================
Semantic execution layer for JARVIS AI OS.
"""
from .semantic_action_registry import semantic_action_registry, SemanticActionEntry
from .app_launcher import app_launcher

__all__ = [
    "semantic_action_registry",
    "SemanticActionEntry",
    "app_launcher"
]
