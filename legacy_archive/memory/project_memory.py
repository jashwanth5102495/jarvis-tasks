
"""
project_memory.py
=================
Persistent storage of project information:
  - Project name
  - Framework used
  - Workspace path
  - Last modified date
  - Workflow history
  - Generated files
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_PROJECTS_FILE = Path(__file__).parent.parent / "config" / "projects.json"


class ProjectMemory:
    """
    Persistent project memory manager.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or _PROJECTS_FILE
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._projects: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load project memory: {e}")
        return {}

    def _save(self) -> None:
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save project memory: {e}")

    def add_project(
        self,
        project_name: str,
        framework: str,
        workspace: str,
        description: str = "",
    ) -> None:
        self._projects[project_name] = {
            "project_name": project_name,
            "framework": framework,
            "workspace": workspace,
            "description": description,
            "last_modified": datetime.now().isoformat(),
            "generated_files": [],
            "workflow_history": [],
        }
        self._save()
        logger.info(f"Added project to memory: {project_name}")

    def get_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        return self._projects.get(project_name)

    def list_projects(self) -> List[Dict[str, Any]]:
        return list(self._projects.values())

    def update_project(self, project_name: str, updates: Dict[str, Any]) -> None:
        if project_name in self._projects:
            self._projects[project_name].update(updates)
            self._projects[project_name]["last_modified"] = datetime.now().isoformat()
            self._save()
            logger.info(f"Updated project: {project_name}")

    def add_generated_file(self, project_name: str, file_path: str) -> None:
        if project_name in self._projects:
            if file_path not in self._projects[project_name]["generated_files"]:
                self._projects[project_name]["generated_files"].append(file_path)
                self._save()
                logger.info(f"Added generated file to project {project_name}: {file_path}")

    def add_workflow_history(self, project_name: str, workflow_id: str, workflow_name: str) -> None:
        if project_name in self._projects:
            entry = {
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "timestamp": datetime.now().isoformat(),
            }
            self._projects[project_name]["workflow_history"].append(entry)
            self._save()


project_memory = ProjectMemory()
