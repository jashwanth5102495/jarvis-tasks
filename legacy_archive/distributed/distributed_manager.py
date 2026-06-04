
"""
distributed_manager.py
======================
Main manager for distributed JARVIS operations.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from distributed.node_registry import node_registry
from distributed.auth_manager import auth_manager
from distributed.encrypted_transport import encrypted_transport
from distributed.remote_executor import remote_executor
from distributed.sync_engine import sync_engine
from distributed.device_router import device_router
from distributed.websocket_gateway import websocket_gateway
from distributed.mobile_api import mobile_api
from distributed.alexa_bridge import alexa_bridge
from distributed.cloud_connector import cloud_connector
from distributed.distributed_scheduler import distributed_scheduler
from distributed.remote_memory import remote_memory

logger = logging.getLogger(__name__)


@dataclass
class DistributedStatus:
    """Current status of the distributed system."""
    is_active: bool = False
    node_count: int = 0
    online_node_count: int = 0
    last_sync: Optional[datetime] = None
    active_executions: int = 0


class DistributedManager:
    """
    Main manager for all distributed JARVIS operations.
    """

    def __init__(self):
        self._status = DistributedStatus()
        self._local_node_id: Optional[str] = None

    def initialize(self, node_name: str = "local", node_type: str = "desktop") -> None:
        """Initialize the distributed system."""
        logger.info("Initializing distributed JARVIS...")
        
        # Register this node
        self._local_node_id = node_registry.register_node(
            node_type=node_type,
            name=node_name,
            capabilities=["computer_control", "coding", "browser", "voice"]
        )
        
        # Start services
        websocket_gateway.start()
        self._status.is_active = True
        self._update_status()
        logger.info(f"Distributed JARVIS initialized as node {self._local_node_id}")

    def shutdown(self) -> None:
        """Shut down the distributed system."""
        logger.info("Shutting down distributed JARVIS...")
        websocket_gateway.stop()
        if self._local_node_id:
            node_registry.update_node_status(self._local_node_id, "offline")
        self._status.is_active = False
        logger.info("Distributed JARVIS shut down")

    def pair_device(self) -> str:
        """Generate a pairing code for a new device."""
        if not self._local_node_id:
            raise RuntimeError("Distributed system not initialized")
        return auth_manager.generate_pairing_code(self._local_node_id)

    def execute_remotely(self, workflow: Dict[str, Any],
                         target_node_id: Optional[str] = None) -> str:
        """Execute a workflow on a remote node."""
        execution_id = remote_executor.execute_remotely(workflow, target_node_id)
        self._update_status()
        return execution_id

    def sync_now(self) -> List[Dict[str, Any]]:
        """Trigger an immediate sync."""
        operations = sync_engine.sync_all()
        self._update_status()
        return [
            {
                "sync_id": op.sync_id,
                "type": op.operation_type,
                "data_type": op.data_type,
                "status": op.status
            }
            for op in operations
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get the current distributed system status."""
        self._update_status()
        return {
            "is_active": self._status.is_active,
            "local_node_id": self._local_node_id,
            "node_count": self._status.node_count,
            "online_node_count": self._status.online_node_count,
            "last_sync": self._status.last_sync.isoformat() if self._status.last_sync else None,
            "active_executions": self._status.active_executions
        }

    def _update_status(self) -> None:
        """Update the internal status object."""
        nodes = node_registry.list_nodes()
        online_nodes = node_registry.list_nodes(only_online=True)
        active_executions = len(remote_executor.list_executions(status="running"))
        
        self._status.node_count = len(nodes)
        self._status.online_node_count = len(online_nodes)
        self._status.last_sync = sync_engine.get_last_sync()
        self._status.active_executions = active_executions


# Module-level singleton
distributed_manager = DistributedManager()
