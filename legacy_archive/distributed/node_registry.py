
"""
node_registry.py
===============
Node registry system for tracking connected devices and their capabilities.
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Represents a connected node/device in the JARVIS ecosystem."""
    node_id: str
    node_type: str  # "desktop", "mobile", "cloud", "iot"
    name: str
    status: str = "offline"  # "online", "offline", "busy"
    capabilities: List[str] = field(default_factory=list)
    last_seen: Optional[datetime] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class NodeRegistry:
    """
    Registry for tracking all connected nodes in the distributed system.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "node_registry.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._nodes: Dict[str, Node] = {}
        self._load()

    def register_node(
        self,
        node_type: str,
        name: str,
        capabilities: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new node or update an existing one.
        Returns the node_id.
        """
        node_id = str(uuid.uuid4())
        node = Node(
            node_id=node_id,
            node_type=node_type,
            name=name,
            status="online",
            capabilities=capabilities or [],
            last_seen=datetime.now(),
            ip_address=ip_address,
            metadata=metadata or {}
        )
        self._nodes[node_id] = node
        self._save()
        logger.info(f"Registered node: {name} ({node_id})")
        return node_id

    def update_node_status(self, node_id: str, status: str) -> bool:
        """Update the status of a registered node."""
        if node_id not in self._nodes:
            logger.warning(f"Node not found: {node_id}")
            return False
        self._nodes[node_id].status = status
        self._nodes[node_id].last_seen = datetime.now()
        self._save()
        logger.info(f"Updated node {node_id} status to {status}")
        return True

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        return self._nodes.get(node_id)

    def list_nodes(self, node_type: Optional[str] = None, only_online: bool = False) -> List[Node]:
        """List all registered nodes, optionally filtered."""
        nodes = list(self._nodes.values())
        if node_type:
            nodes = [n for n in nodes if n.node_type == node_type]
        if only_online:
            nodes = [n for n in nodes if n.status == "online"]
        return nodes

    def find_nodes_by_capability(self, capability: str) -> List[Node]:
        """Find all online nodes that support a specific capability."""
        return [
            node for node in self._nodes.values()
            if node.status == "online" and capability in node.capabilities
        ]

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the registry."""
        if node_id in self._nodes:
            del self._nodes[node_id]
            self._save()
            logger.info(f"Removed node: {node_id}")
            return True
        return False

    def _save(self) -> None:
        """Save the node registry to disk."""
        data = {
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "name": node.name,
                    "status": node.status,
                    "capabilities": node.capabilities,
                    "last_seen": node.last_seen.isoformat() if node.last_seen else None,
                    "ip_address": node.ip_address,
                    "metadata": node.metadata
                }
                for node in self._nodes.values()
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load the node registry from disk."""
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            for node_data in data.get("nodes", []):
                node = Node(
                    node_id=node_data["node_id"],
                    node_type=node_data["node_type"],
                    name=node_data["name"],
                    status=node_data["status"],
                    capabilities=node_data.get("capabilities", []),
                    last_seen=datetime.fromisoformat(node_data["last_seen"]) if node_data.get("last_seen") else None,
                    ip_address=node_data.get("ip_address"),
                    metadata=node_data.get("metadata", {})
                )
                self._nodes[node.node_id] = node
            logger.info(f"Loaded {len(self._nodes)} nodes from registry")
        except Exception as e:
            logger.error(f"Failed to load node registry: {e}")


# Module-level singleton
node_registry = NodeRegistry()
