
"""
conversation_context.py
====================
Conversation context system for JARVIS. Tracks recent topics,
active workflows, current applications, and referenced entities.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from jarvis.memory.project_memory import project_memory
from jarvis.memory.preference_memory import preference_memory
from jarvis.memory.workflow_checkpoint import workflow_checkpoint
from jarvis.voice.voice_memory import voice_memory

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context data for a conversation."""
    recent_topics: List[str] = field(default_factory=list)
    active_workflow: Optional[Dict[str, Any]] = None
    active_application: Optional[str] = None
    referenced_entities: List[str] = field(default_factory=list)
    pending_actions: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class ConversationContextBuilder:
    """
    Builds context for conversations with JARVIS.
    Tracks topics, workflows, applications, and referenced entities.
    """

    def __init__(self):
        self._context = ConversationContext()
        self._topic_timeout = timedelta(minutes=30)

    def build_context(self, current_message: str) -> Dict[str, Any]:
        """Build a comprehensive context dictionary."""
        # Update context with current message
        self._extract_topics(current_message)
        
        # Get memory context
        project_context = self._get_project_context()
        preference_context = self._get_preference_context()
        workflow_context = self._get_workflow_context()
        
        # Build full context
        full_context = {
            "recent_topics": self._context.recent_topics,
            "active_workflow": self._context.active_workflow,
            "active_application": self._context.active_application,
            "referenced_entities": self._context.referenced_entities,
            "pending_actions": self._context.pending_actions,
            **project_context,
            **preference_context,
            **workflow_context
        }
        
        self._context.last_updated = datetime.now()
        return full_context

    def _extract_topics(self, message: str) -> None:
        """Extract topics from a message."""
        message_lower = message.lower()
        
        # Simple topic extraction (can be enhanced with NLP)
        topics = []
        
        if "chrome" in message_lower or "browser" in message_lower:
            topics.append("chrome")
            self._context.active_application = "chrome"
        elif "vscode" in message_lower or "code" in message_lower:
            topics.append("vscode")
            self._context.active_application = "vscode"
        elif "screenshot" in message_lower:
            topics.append("screenshot")
        elif "search" in message_lower:
            topics.append("search")
        elif "project" in message_lower:
            topics.append("project")
        
        # Add to recent topics (avoid duplicates)
        for topic in topics:
            if topic not in self._context.recent_topics:
                self._context.recent_topics.insert(0, topic)
                # Keep only last 10 topics
                self._context.recent_topics = self._context.recent_topics[:10]

    def _get_project_context(self) -> Dict[str, Any]:
        """Get project-related context."""
        projects = project_memory.list_projects()
        return {
            "recent_projects": projects[:5],
            "active_project": projects[0] if projects else None
        }

    def _get_preference_context(self) -> Dict[str, Any]:
        """Get user preference context."""
        return {
            "preferences": preference_memory.get_all()
        }

    def _get_workflow_context(self) -> Dict[str, Any]:
        """Get workflow-related context."""
        interrupted = workflow_checkpoint.list_interrupted_workflows()
        return {
            "interrupted_workflows": interrupted[:3]
        }

    def set_active_workflow(self, workflow: Dict[str, Any]) -> None:
        """Set the currently active workflow."""
        self._context.active_workflow = workflow
        logger.info(f"Set active workflow: {workflow.get('id', 'unknown')}")

    def add_referenced_entity(self, entity: str) -> None:
        """Add a referenced entity to context."""
        if entity not in self._context.referenced_entities:
            self._context.referenced_entities.append(entity)

    def add_pending_action(self, action: Dict[str, Any]) -> None:
        """Add a pending action to context."""
        self._context.pending_actions.append(action)

    def clear(self) -> None:
        """Clear the conversation context."""
        self._context = ConversationContext()
        logger.info("Conversation context cleared")


# Module-level singleton
conversation_context = ConversationContextBuilder()

