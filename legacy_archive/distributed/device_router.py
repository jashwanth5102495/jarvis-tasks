
"""
device_router.py
===============
Device router for selecting optimal nodes for workflow execution.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from distributed.node_registry import node_registry, Node

logger = logging.getLogger(__name__)


class DeviceRouter:
    """
    Routes workflows to the optimal execution node based on capabilities.
    """

    def __init__(self):
        self._capability_priorities = {
            "gpu_tasks": ["desktop", "cloud"],
            "lightweight": ["mobile", "desktop"],
            "computer_control": ["desktop"],
            "coding": ["desktop", "cloud"]
        }

    def select_node_for_workflow(
        self,
        workflow: Dict[str, Any],
        preferred_node_id: Optional[str] = None
    ) -> Optional[Node]:
        """
        Select the best node to execute a workflow.
        """
        # If a preferred node is specified and it's available, use it
        if preferred_node_id:
            node = node_registry.get_node(preferred_node_id)
            if node and node.status == "online":
                logger.info(f"Using preferred node: {preferred_node_id}")
                return node

        # Determine required capabilities from the workflow
        required_capabilities = self._extract_required_capabilities(workflow)

        # Find all nodes that match the requirements
        candidates = node_registry.list_nodes(only_online=True)
        matching_nodes = []

        for node in candidates:
            has_all = True
            for cap in required_capabilities:
                if cap not in node.capabilities:
                    has_all = False
                    break
            if has_all:
                matching_nodes.append(node)

        if not matching_nodes:
            logger.warning("No matching nodes found for workflow")
            return None

        # Select the best matching node based on priorities
        return self._rank_nodes(matching_nodes, workflow)

    def _extract_required_capabilities(self, workflow: Dict[str, Any]) -> List[str]:
        """Extract required capabilities from a workflow definition."""
        capabilities = []
        for step in workflow.get("steps", []):
            action = step.get("action", "")
            if action in ["open_application", "execute_code", "computer_control"]:
                capabilities.append("computer_control")
            if action in ["code_generation", "debug_code"]:
                capabilities.append("coding")
            if action in ["browser_automation"]:
                capabilities.append("browser")
        return capabilities if capabilities else ["lightweight"]

    def _rank_nodes(self, nodes: List[Node], workflow: Dict[str, Any]) -> Optional[Node]:
        """Rank matching nodes by priority."""
        # First, categorize the workflow type
        workflow_type = self._categorize_workflow(workflow)

        # Get priority order for this type
        priority_order = self._capability_priorities.get(workflow_type, ["desktop", "cloud", "mobile"])

        # Select the first node that matches the highest priority type
        for node_type in priority_order:
            for node in nodes:
                if node.node_type == node_type:
                    logger.info(f"Selected node {node.name} ({node.node_id})")
                    return node

        # Fallback to first available node
        return nodes[0] if nodes else None

    def _categorize_workflow(self, workflow: Dict[str, Any]) -> str:
        """Categorize a workflow type."""
        for step in workflow.get("steps", []):
            if "gpu" in step.get("params", {}):
                return "gpu_tasks"
            if "coding" in step.get("action", ""):
                return "coding"
            if "computer" in step.get("action", ""):
                return "computer_control"
        return "lightweight"


# Module-level singleton
device_router = DeviceRouter()
