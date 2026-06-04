
"""
WebSocket Server Module
=======================
WebSocket server for real-time JARVIS communication
"""
import logging
import asyncio
import json
from typing import Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()

