
"""
auth_manager.py
===============
Authentication and authorization system for distributed JARVIS.
Handles device pairing, token validation, and permission management.
"""

from __future__ import annotations

import logging
import secrets
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """Represents an authentication token."""
    token_id: str
    node_id: str
    token_hash: str
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class DevicePairing:
    """Represents a paired device."""
    pairing_id: str
    node_id: str
    pairing_code: str
    is_paired: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class AuthManager:
    """
    Manages authentication, authorization, and device pairing for distributed JARVIS.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or Path(__file__).parent.parent / "data" / "auth_data.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._tokens: Dict[str, AuthToken] = {}
        self._pairings: Dict[str, DevicePairing] = {}
        self._load()

    def generate_pairing_code(self, node_id: str, validity_minutes: int = 10) -> str:
        """Generate a pairing code for a new device."""
        pairing_code = secrets.token_hex(3).upper()  # 6-character code
        pairing_id = secrets.token_urlsafe(16)
        pairing = DevicePairing(
            pairing_id=pairing_id,
            node_id=node_id,
            pairing_code=pairing_code,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=validity_minutes)
        )
        self._pairings[pairing_id] = pairing
        self._save()
        logger.info(f"Generated pairing code for node {node_id}")
        return pairing_code

    def validate_pairing_code(self, pairing_code: str) -> Optional[str]:
        """Validate a pairing code and return the node_id if valid."""
        for pairing in list(self._pairings.values()):
            if pairing.is_paired:
                continue
            if pairing.expires_at and datetime.now() > pairing.expires_at:
                del self._pairings[pairing.pairing_id]
                continue
            if pairing.pairing_code == pairing_code.upper():
                pairing.is_paired = True
                self._save()
                logger.info(f"Pairing code validated for node {pairing.node_id}")
                return pairing.node_id
        logger.warning(f"Invalid pairing code: {pairing_code}")
        return None

    def generate_auth_token(self, node_id: str, permissions: Optional[List[str]] = None, expires_in_hours: int = 720) -> str:
        """Generate a new authentication token for a node."""
        token_id = secrets.token_urlsafe(32)
        token_secret = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(token_secret.encode()).hexdigest()
        token = AuthToken(
            token_id=token_id,
            node_id=node_id,
            token_hash=token_hash,
            permissions=permissions or [],
            expires_at=datetime.now() + timedelta(hours=expires_in_hours)
        )
        self._tokens[token_id] = token
        self._save()
        logger.info(f"Generated auth token for node {node_id}")
        # Return the token in format: token_id.token_secret
        return f"{token_id}.{token_secret}"

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an authentication token and return its info if valid."""
        try:
            token_id, token_secret = token.split(".", 1)
        except ValueError:
            logger.warning("Invalid token format")
            return None
        if token_id not in self._tokens:
            logger.warning(f"Token not found: {token_id}")
            return None
        stored = self._tokens[token_id]
        if stored.expires_at and datetime.now() > stored.expires_at:
            del self._tokens[token_id]
            self._save()
            logger.warning("Token has expired")
            return None
        computed_hash = hashlib.sha256(token_secret.encode()).hexdigest()
        if computed_hash != stored.token_hash:
            logger.warning("Token hash mismatch")
            return None
        logger.info(f"Validated token for node {stored.node_id}")
        return {
            "node_id": stored.node_id,
            "permissions": stored.permissions,
            "created_at": stored.created_at,
            "expires_at": stored.expires_at
        }

    def check_permission(self, token_info: Dict[str, Any], permission: str) -> bool:
        """Check if a token has a specific permission."""
        return permission in token_info.get("permissions", [])

    def revoke_token(self, token_id: str) -> bool:
        """Revoke an authentication token."""
        if token_id in self._tokens:
            del self._tokens[token_id]
            self._save()
            logger.info(f"Revoked token: {token_id}")
            return True
        return False

    def _save(self) -> None:
        """Save authentication data to disk."""
        data = {
            "tokens": [
                {
                    "token_id": t.token_id,
                    "node_id": t.node_id,
                    "token_hash": t.token_hash,
                    "permissions": t.permissions,
                    "created_at": t.created_at.isoformat(),
                    "expires_at": t.expires_at.isoformat() if t.expires_at else None
                }
                for t in self._tokens.values()
            ],
            "pairings": [
                {
                    "pairing_id": p.pairing_id,
                    "node_id": p.node_id,
                    "pairing_code": p.pairing_code,
                    "is_paired": p.is_paired,
                    "created_at": p.created_at.isoformat(),
                    "expires_at": p.expires_at.isoformat() if p.expires_at else None
                }
                for p in self._pairings.values()
            ]
        }
        with open(self._storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self) -> None:
        """Load authentication data from disk."""
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r") as f:
                data = json.load(f)
            for t_data in data.get("tokens", []):
                token = AuthToken(
                    token_id=t_data["token_id"],
                    node_id=t_data["node_id"],
                    token_hash=t_data["token_hash"],
                    permissions=t_data.get("permissions", []),
                    created_at=datetime.fromisoformat(t_data["created_at"]),
                    expires_at=datetime.fromisoformat(t_data["expires_at"]) if t_data.get("expires_at") else None
                )
                self._tokens[token.token_id] = token
            for p_data in data.get("pairings", []):
                pairing = DevicePairing(
                    pairing_id=p_data["pairing_id"],
                    node_id=p_data["node_id"],
                    pairing_code=p_data["pairing_code"],
                    is_paired=p_data.get("is_paired", False),
                    created_at=datetime.fromisoformat(p_data["created_at"]),
                    expires_at=datetime.fromisoformat(p_data["expires_at"]) if p_data.get("expires_at") else None
                )
                self._pairings[pairing.pairing_id] = pairing
            logger.info(f"Loaded {len(self._tokens)} tokens and {len(self._pairings)} pairings")
        except Exception as e:
            logger.error(f"Failed to load auth data: {e}")


# Module-level singleton
auth_manager = AuthManager()
