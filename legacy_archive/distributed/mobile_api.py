
"""
mobile_api.py
============
Mobile API layer for JARVIS mobile app integration.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from distributed.auth_manager import auth_manager
from distributed.remote_executor import remote_executor
from distributed.sync_engine import sync_engine
from voice.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)


class MobileAPI:
    """
    API for mobile app interaction with JARVIS.
    """

    def __init__(self):
        pass

    def send_command(self, command: str, auth_token: str) -> Dict[str, Any]:
        """Process a command from the mobile app."""
        # Validate auth token
        token_info = auth_manager.validate_token(auth_token)
        if not token_info:
            return {"success": False, "error": "Invalid authentication"}
        logger.info(f"Mobile command received: {command}")

        # Process with conversation manager
        response = conversation_manager.process_message(command)
        return {"success": True, "response": response}

    def get_workflow_status(self, execution_id: str, auth_token: str) -> Dict[str, Any]:
        """Get the status of a remote execution."""
        token_info = auth_manager.validate_token(auth_token)
        if not token_info:
            return {"success": False, "error": "Invalid authentication"}
        status = remote_executor.get_execution_status(execution_id)
        if status:
            return {"success": True, "status": status}
        return {"success": False, "error": "Execution not found"}

    def list_workflows(self, auth_token: str) -> Dict[str, Any]:
        """List all active and recent workflows."""
        token_info = auth_manager.validate_token(auth_token)
        if not token_info:
            return {"success": False, "error": "Invalid authentication"}
        executions = remote_executor.list_executions()
        return {"success": True, "workflows": executions}

    def trigger_sync(self, auth_token: str) -> Dict[str, Any]:
        """Trigger a memory sync operation."""
        token_info = auth_manager.validate_token(auth_token)
        if not token_info:
            return {"success": False, "error": "Invalid authentication"}
        operations = sync_engine.sync_all()
        return {
            "success": True,
            "operations": [
                {
                    "sync_id": op.sync_id,
                    "type": op.operation_type,
                    "data_type": op.data_type,
                    "status": op.status
                }
                for op in operations
            ]
        }

    def send_notification(self, notification: Dict[str, Any], auth_token: str) -> Dict[str, Any]:
        """Send a notification to the mobile device."""
        token_info = auth_manager.validate_token(auth_token)
        if not token_info:
            return {"success": False, "error": "Invalid authentication"}
        logger.info(f"Sending notification to mobile: {notification}")
        return {"success": True, "notification_id": "mock_notification_id"}


# Module-level singleton
mobile_api = MobileAPI()
