
"""
capability_tracker.py
===================
Capability tracking system for JARVIS evolution.
Tracks learned technologies, skill maturity, and evolution history.
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
class Capability:
    """Represents a tracked capability."""
    name: str
    maturity: str  # learning, basic, intermediate, advanced
    success_rate: float
    total_uses: int
    last_used: Optional[datetime] = None
    first_learned: datetime = field(default_factory=datetime.now)


class CapabilityTracker:
    """
    Tracks JARVIS's capabilities and evolution history.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "capability_tracker.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._capabilities: Dict[str, Capability] = {}
        self._load()

    def record_upgrade(self, upgrade_result: Dict[str, Any]) -> None:
        """Record an upgrade event."""
        logger.info(f"Recording upgrade: {upgrade_result}")
        # Mock implementation - in real system, this would update capabilities
        self._save()

    def add_capability(self, capability: Capability) -> None:
        """Add a capability to tracking."""
        self._capabilities[capability.name] = capability
        self._save()
        logger.info(f"Added capability: {capability.name}")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of capabilities."""
        return {
            "total_capabilities": len(self._capabilities),
            "capabilities": [
                {
                    "name": c.name,
                    "maturity": c.maturity,
                    "success_rate": c.success_rate,
                    "total_uses": c.total_uses
                }
                for c in self._capabilities.values()
            ]
        }

    def _save(self) -> None:
        data = {
            "capabilities": [
                {
                    "name": c.name,
                    "maturity": c.maturity,
                    "success_rate": c.success_rate,
                    "total_uses": c.total_uses,
                    "last_used": c.last_used.isoformat() if c.last_used else None,
                    "first_learned": c.first_learned.isoformat()
                }
                for c in self._capabilities.values()
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            for c_data in data.get("capabilities", []):
                cap = Capability(
                    name=c_data["name"],
                    maturity=c_data["maturity"],
                    success_rate=c_data["success_rate"],
                    total_uses=c_data["total_uses"],
                    last_used=datetime.fromisoformat(c_data["last_used"]) if c_data.get("last_used") else None,
                    first_learned=datetime.fromisoformat(c_data["first_learned"])
                )
                self._capabilities[cap.name] = cap
            logger.info(f"Loaded {len(self._capabilities)} capabilities")
        except Exception as e:
            logger.error(f"Failed to load capability tracker: {e}")


# Module-level singleton
capability_tracker = CapabilityTracker()
