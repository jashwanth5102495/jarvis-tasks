
"""
websocket_gateway.py
===================
WebSocket gateway for real-time distributed communication.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConnectedClient:
    """Represents a connected WebSocket client."""
    client_id: str
    node_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    is_authenticated: bool = False


class WebSocketGateway:
    """
    WebSocket gateway for real-time communication between nodes.
    """

    def __init__(self):
        self._clients: Dict[str, ConnectedClient] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._is_running = False

    def start(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        """Start the WebSocket server."""
        if self._is_running:
            logger.warning("WebSocket gateway already running")
            return
        self._is_running = True
        logger.info(f"WebSocket gateway starting on {host}:{port}")
        # In real implementation, use websockets library
        # Mock startup for now

    def stop(self) -> None:
        """Stop the WebSocket server."""
        self._is_running = False
        logger.info("WebSocket gateway stopped")

    def connect_client(self, client_id: str) -> None:
        """Register a new client connection."""
        client = ConnectedClient(client_id=client_id)
        self._clients[client_id] = client
        logger.info(f"Client connected: {client_id}")

    def disconnect_client(self, client_id: str) -> None:
        """Remove a disconnected client."""
        if client_id in self._clients:
            del self._clients[client_id]
            logger.info(f"Client disconnected: {client_id}")

    def authenticate_client(self, client_id: str, node_id: str) -> bool:
        """Authenticate a connected client."""
        if client_id not in self._clients:
            return False
        self._clients[client_id].node_id = node_id
        self._clients[client_id].is_authenticated = True
        logger.info(f"Client {client_id} authenticated as node {node_id}")
        return True

    def send_message(self, recipient_client_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a connected client."""
        if recipient_client_id not in self._clients:
            logger.warning(f"Client not found: {recipient_client_id}")
            return False
        client = self._clients[recipient_client_id]
        if not client.is_authenticated:
            logger.warning("Cannot send to unauthenticated client")
            return False
        logger.info(f"Sending message to {recipient_client_id}")
        return True

    def broadcast_message(self, message: Dict[str, Any], only_authenticated: bool = True) -> int:
        """Broadcast a message to all connected clients."""
        count = 0
        for client in self._clients.values():
            if not only_authenticated or client.is_authenticated:
                self.send_message(client.client_id, message)
                count += 1
        logger.info(f"Broadcast message to {count} clients")
        return count

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type."""
        self._message_handlers[message_type] = handler
        logger.info(f"Registered handler for {message_type}")

    def handle_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """Handle an incoming message from a client."""
        if client_id not in self._clients:
            return
        msg_type = message.get("type", "unknown")
        if msg_type in self._message_handlers:
            try:
                self._message_handlers[msg_type](client_id, message)
            except Exception as e:
                logger.error(f"Error handling message: {e}")


# Module-level singleton
websocket_gateway = WebSocketGateway()
