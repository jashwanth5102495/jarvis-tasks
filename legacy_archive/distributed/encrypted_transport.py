
"""
encrypted_transport.py
=====================
Encrypted communication layer for distributed JARVIS.
Handles secure messaging between nodes.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import base64
import hashlib
import secrets

logger = logging.getLogger(__name__)


@dataclass
class EncryptedMessage:
    """Represents an encrypted message between nodes."""
    message_id: str
    sender_node_id: str
    recipient_node_id: str
    encrypted_payload: str
    timestamp: datetime = field(default_factory=datetime.now)
    signature: Optional[str] = None


class EncryptedTransport:
    """
    Provides encrypted communication between JARVIS nodes.
    Note: This is a mock implementation for demonstration.
    In production, use TLS, AES-GCM, or other standard protocols.
    """

    def __init__(self):
        self._message_handlers: Dict[str, Callable] = {}
        self._shared_secrets: Dict[str, str] = {}

    def generate_shared_secret(self) -> str:
        """Generate a new shared secret for encryption."""
        return secrets.token_hex(32)

    def set_shared_secret(self, node_id: str, secret: str) -> None:
        """Set the shared secret for a node."""
        self._shared_secrets[node_id] = secret
        logger.info(f"Set shared secret for node {node_id}")

    def _encrypt(self, payload: Dict[str, Any], secret: str) -> str:
        """Encrypt a payload (mock implementation)."""
        payload_str = json.dumps(payload)
        # Mock encryption - in production use real AES
        combined = f"{payload_str}.{secret}"
        encrypted = base64.b64encode(combined.encode()).decode()
        return encrypted

    def _decrypt(self, encrypted: str, secret: str) -> Optional[Dict[str, Any]]:
        """Decrypt a payload (mock implementation)."""
        try:
            decoded = base64.b64decode(encrypted.encode()).decode()
            payload_str, _ = decoded.rsplit(".", 1)
            return json.loads(payload_str)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def _sign(self, data: str, secret: str) -> str:
        """Sign data (mock implementation)."""
        combined = f"{data}.{secret}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def send_message(
        self,
        sender_node_id: str,
        recipient_node_id: str,
        payload: Dict[str, Any],
        message_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Send an encrypted message to a node.
        Returns the message ID.
        """
        if recipient_node_id not in self._shared_secrets:
            logger.warning(f"No shared secret for node {recipient_node_id}")
            return None
        secret = self._shared_secrets[recipient_node_id]
        message_id = message_id or secrets.token_urlsafe(16)
        encrypted_payload = self._encrypt(payload, secret)
        signature = self._sign(f"{message_id}{sender_node_id}{recipient_node_id}{encrypted_payload}", secret)
        message = EncryptedMessage(
            message_id=message_id,
            sender_node_id=sender_node_id,
            recipient_node_id=recipient_node_id,
            encrypted_payload=encrypted_payload,
            signature=signature
        )
        logger.info(f"Sent encrypted message {message_id} to {recipient_node_id}")
        # In a real implementation, this would send over the network
        return message_id

    def receive_message(
        self,
        message: EncryptedMessage,
        current_node_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Receive and decrypt a message.
        Returns the payload if valid.
        """
        if message.recipient_node_id != current_node_id:
            logger.warning("Message not intended for this node")
            return None
        if message.sender_node_id not in self._shared_secrets:
            logger.warning(f"No shared secret for sender {message.sender_node_id}")
            return None
        secret = self._shared_secrets[message.sender_node_id]
        expected_signature = self._sign(
            f"{message.message_id}{message.sender_node_id}{message.recipient_node_id}{message.encrypted_payload}",
            secret
        )
        if message.signature and message.signature != expected_signature:
            logger.warning("Message signature invalid")
            return None
        payload = self._decrypt(message.encrypted_payload, secret)
        if payload:
            logger.info(f"Received and decrypted message {message.message_id}")
            # Call any registered handlers
            msg_type = payload.get("type", "unknown")
            if msg_type in self._message_handlers:
                try:
                    self._message_handlers[msg_type](payload, message.sender_node_id)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")
        return payload

    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type."""
        self._message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")


# Module-level singleton
encrypted_transport = EncryptedTransport()
