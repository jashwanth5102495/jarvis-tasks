
"""
semantic_retriever.py
=====================
Retrieves relevant memory items using semantic search.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from llm.vector_store import vector_store
from memory.project_memory import project_memory
from memory.preference_memory import preference_memory
from memory.workflow_checkpoint import workflow_checkpoint

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """
    Retrieves relevant memory context using semantic search.
    """

    def retrieve_relevant_projects(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve projects relevant to the query."""
        # Add all projects to vector store for search
        for project in project_memory.list_projects():
            text = f"Project: {project['project_name']}\nDescription: {project.get('description', '')}\nStack: {project.get('framework', '')}"
            vector_store.add_document(
                text=text,
                metadata={"type": "project", "project_id": project.get("project_name")},
                doc_id=f"project_{project.get('project_name')}",
            )

        # Search
        results = vector_store.search(query, limit=limit)
        projects = []
        for doc in results:
            if doc.metadata.get("type") == "project":
                project_data = project_memory.get_project(doc.metadata.get("project_id", ""))
                if project_data:
                    projects.append(project_data)
        return projects

    def retrieve_relevant_workflows(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve workflows relevant to the query."""
        # Add interrupted workflows to store
        for workflow in workflow_checkpoint.list_interrupted_workflows():
            text = f"Workflow: {workflow.get('goal', '')}\nStatus: {workflow.get('status')}"
            vector_store.add_document(
                text=text,
                metadata={"type": "workflow", "workflow_id": workflow.get("workflow_id")},
                doc_id=f"workflow_{workflow.get('workflow_id')}",
            )

        results = vector_store.search(query, limit=limit)
        workflows = []
        for doc in results:
            if doc.metadata.get("type") == "workflow":
                workflows.append(doc.metadata)
        return workflows

    def retrieve_preferences(self) -> Dict[str, Any]:
        """Retrieve all user preferences."""
        return preference_memory.get_all()

    def retrieve_all(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Retrieve all relevant context for a query."""
        return {
            "projects": self.retrieve_relevant_projects(query, limit=limit),
            "workflows": self.retrieve_relevant_workflows(query, limit=limit),
            "preferences": self.retrieve_preferences(),
        }


# Module-level singleton
semantic_retriever = SemanticRetriever()

