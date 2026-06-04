
"""
alexa_bridge.py
==============
Alexa skill integration bridge.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from distributed.auth_manager import auth_manager
from voice.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)


class AlexaBridge:
    """
    Bridge between Alexa and JARVIS.
    """

    def __init__(self):
        pass

    def handle_intent(self, intent_request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming intent from Alexa."""
        intent_name = intent_request.get("request", {}).get("intent", {}).get("name", "")
        logger.info(f"Received Alexa intent: {intent_name}")

        # Validate access token
        access_token = intent_request.get("context", {}).get("System", {}).get("user", {}).get("accessToken")
        if not access_token:
            return self._build_error_response("Authentication required")

        # Validate token with auth manager
        token_info = auth_manager.validate_token(access_token)
        if not token_info:
            return self._build_error_response("Invalid authentication")

        # Process intent
        response_text = ""
        if intent_name == "JarvisCommandIntent":
            command = intent_request.get("request", {}).get("intent", {}).get("slots", {}).get("command", {}).get("value", "")
            response = conversation_manager.process_message(command)
            # Handle both string and dict responses
            if isinstance(response, str):
                response_text = response
            else:
                response_text = response.get("response", "I'll help with that right away.")
        elif intent_name == "AMAZON.StopIntent":
            response_text = "Goodbye!"
        elif intent_name == "AMAZON.CancelIntent":
            response_text = "Cancelled."
        else:
            response_text = "Sorry, I didn't understand that."

        return self._build_response(response_text)

    def _build_response(self, text: str, end_session: bool = True) -> Dict[str, Any]:
        """Build an Alexa response."""
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": text
                },
                "shouldEndSession": end_session
            }
        }

    def _build_error_response(self, error_text: str) -> Dict[str, Any]:
        """Build an error response for Alexa."""
        return self._build_response(error_text)


# Module-level singleton
alexa_bridge = AlexaBridge()
