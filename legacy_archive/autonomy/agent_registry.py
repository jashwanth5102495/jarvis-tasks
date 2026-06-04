
"""
agent_registry.py
=================
Tracks active, paused, completed, and failed autonomous agents.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_REGISTRY_FILE = Path(__file__).parent.parent / "config" / "agent_registry.json"


class AgentRegistry:
    """
    Registry for autonomous agents.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or _REGISTRY_FILE
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._agents: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        try:
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load agent registry: {e}")
        return {}

    def _save(self) -> None:
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._agents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save agent registry: {e}")

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        description: str = "",
    ) -> None:
        self._agents[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "finished_at": None,
            "last_run": None,
            "metadata": {},
        }
        self._save()
        logger.info(f"Registered agent: {agent_id}")

    def update_agent_status(self, agent_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if agent_id in self._agents:
            self._agents[agent_id]["status"] = status
            if status == "running" and not self._agents[agent_id]["started_at"]:
                self._agents[agent_id]["started_at"] = datetime.now().isoformat()
            if status in ("completed", "failed"):
                self._agents[agent_id]["finished_at"] = datetime.now().isoformat()
            if status in ("running", "completed"):
                self._agents[agent_id]["last_run"] = datetime.now().isoformat()
            if metadata:
                self._agents[agent_id]["metadata"].update(metadata)
            self._save()
            logger.info(f"Updated agent {agent_id} status to {status}")

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    def list_agents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        agents = list(self._agents.values())
        if status:
            return [a for a in agents if a["status"] == status]
        return agents


agent_registry = AgentRegistry()
