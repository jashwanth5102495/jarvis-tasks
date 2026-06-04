
"""
skill_registry.py
=================
Registry for learned skills and their capabilities.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """Represents a learned skill."""
    skill_id: str
    name: str
    description: str
    status: str = "pending"  # pending, validated, active, deprecated
    source: str = ""
    confidence: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SkillRegistry:
    """
    Registry of all learned skills.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "skill_registry.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._skills: Dict[str, Skill] = {}
        self._load()

    def register_skill(self, skill: Skill) -> None:
        """Register a new skill."""
        self._skills[skill.skill_id] = skill
        self._save()
        logger.info(f"Registered skill: {skill.name}")

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        return self._skills.get(skill_id)

    def list_skills(self, status: Optional[str] = None) -> List[Skill]:
        """List all skills, optionally filtered by status."""
        skills = list(self._skills.values())
        if status:
            skills = [s for s in skills if s.status == status]
        return skills

    def update_skill_status(self, skill_id: str, status: str) -> None:
        """Update a skill's status."""
        skill = self._skills.get(skill_id)
        if skill:
            skill.status = status
            skill.updated_at = datetime.now()
            self._save()
            logger.info(f"Updated skill {skill.name} status to {status}")

    def _save(self) -> None:
        """Save skill registry to disk."""
        data = {
            "skills": [
                {
                    "skill_id": s.skill_id,
                    "name": s.name,
                    "description": s.description,
                    "status": s.status,
                    "source": s.source,
                    "confidence": s.confidence,
                    "dependencies": s.dependencies,
                    "capabilities": s.capabilities,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat()
                }
                for s in self._skills.values()
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load skill registry from disk."""
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            for s_data in data.get("skills", []):
                skill = Skill(
                    skill_id=s_data["skill_id"],
                    name=s_data["name"],
                    description=s_data["description"],
                    status=s_data["status"],
                    source=s_data["source"],
                    confidence=s_data["confidence"],
                    dependencies=s_data.get("dependencies", []),
                    capabilities=s_data.get("capabilities", []),
                    created_at=datetime.fromisoformat(s_data["created_at"]),
                    updated_at=datetime.fromisoformat(s_data["updated_at"])
                )
                self._skills[skill.skill_id] = skill
            logger.info(f"Loaded {len(self._skills)} skills")
        except Exception as e:
            logger.error(f"Failed to load skill registry: {e}")


# Module-level singleton
skill_registry = SkillRegistry()
