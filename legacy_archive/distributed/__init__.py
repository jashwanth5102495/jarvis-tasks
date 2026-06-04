
"""
Distributed AI Operating System module for JARVIS.
This module handles multi-device synchronization, remote execution,
cloud orchestration, mobile integration, and distributed agents.
"""

from distributed.distributed_manager import distributed_manager
from distributed.node_registry import node_registry
from distributed.remote_executor import remote_executor
from distributed.sync_engine import sync_engine
from distributed.auth_manager import auth_manager
from distributed.encrypted_transport import encrypted_transport
from distributed.websocket_gateway import websocket_gateway
from distributed.device_router import device_router
from distributed.remote_memory import remote_memory
from distributed.mobile_api import mobile_api
from distributed.alexa_bridge import alexa_bridge
from distributed.cloud_connector import cloud_connector
from distributed.distributed_scheduler import distributed_scheduler

__all__ = [
    "distributed_manager",
    "node_registry",
    "remote_executor",
    "sync_engine",
    "auth_manager",
    "encrypted_transport",
    "websocket_gateway",
    "device_router",
    "remote_memory",
    "mobile_api",
    "alexa_bridge",
    "cloud_connector",
    "distributed_scheduler"
]
