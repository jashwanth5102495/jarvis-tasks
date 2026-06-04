
"""
context_builder.py
==================
Builds comprehensive context for LLM reasoning from JARVIS's memory systems.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from jarvis.memory.project_memory import project_memory
from jarvis.memory.preference_memory import preference_memory
from jarvis.memory.workflow_checkpoint import workflow_checkpoint
from jarvis.execution.execution_history import execution_history
from jarvis.memory.artifact_memory import artifact_memory

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds LLM-ready context from all memory systems.
    """

    def build_context(
        self,
        goal: str,
        include_project: bool = True,
        include_preferences: bool = True,
        include_workflow: bool = True,
        include_history: bool = True,
        include_artifacts: bool = True,
    ) -> Dict[str, Any]:
        """
        Build a comprehensive context dictionary for LLM reasoning.
        """
        context = {"goal": goal}

        if include_project:
            projects = project_memory.list_projects()
            context["project_memory"] = projects
            context["active_project"] = projects[0] if projects else None

        if include_preferences:
            context["user_preferences"] = preference_memory.get_all()

        if include_workflow:
            interrupted = workflow_checkpoint.list_interrupted_workflows()
            if interrupted:
                context["interrupted_workflows"] = interrupted

        if include_history:
            context["recent_history"] = execution_history.get_today_history()[-10:]

        if include_artifacts:
            context["recent_artifacts"] = artifact_memory.list_artifacts()[-10:]

        logger.debug("Context built successfully")
        return context

    def build_simple_context(self, goal: str) -> Dict[str, Any]:
        """Build a lightweight context for quick responses."""
        return self.build_context(
            goal=goal,
            include_project=True,
            include_preferences=True,
            include_workflow=True,
            include_history=False,
            include_artifacts=False,
        )


# Module-level singleton
context_builder = ContextBuilder()

