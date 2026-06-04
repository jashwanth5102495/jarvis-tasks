
"""
conversation_manager.py
===================
Conversation management system for JARVIS. Handles multi-turn conversations,
context maintenance, follow-up questions, and memory continuity.
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from jarvis.voice.conversation_context import conversation_context
from jarvis.voice.voice_memory import voice_memory
from jarvis.llm.reasoning_engine import reasoning_engine
from jarvis.llm.prompt_engine import prompt_engine

logger = logging.getLogger(__name__)


@dataclass
class Conversation:
    """Represents a single conversation session."""
    id: str
    start_time: datetime
    last_updated: datetime
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    Manages conversations with JARVIS.
    Handles multi-turn interactions, context tracking, and response generation.
    """

    def __init__(self):
        self._current_conversation: Optional[Conversation] = None
        self._conversations: Dict[str, Conversation] = {}

    def start_conversation(self) -> str:
        """Start a new conversation."""
        conv_id = str(uuid.uuid4())
        now = datetime.now()
        
        conversation = Conversation(
            id=conv_id,
            start_time=now,
            last_updated=now
        )
        
        self._conversations[conv_id] = conversation
        self._current_conversation = conversation
        
        logger.info(f"Started new conversation: {conv_id}")
        return conv_id

    def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a user message and generate a response."""
        if not self._current_conversation:
            self.start_conversation()
        
        # Add user message to conversation
        self._add_message("user", message)
        
        # Build context
        full_context = conversation_context.build_context(message)
        if context:
            full_context.update(context)
        
        # Get response from reasoning engine
        try:
            # First, try LLM-based response
            plan = reasoning_engine.plan_workflow(message, use_llm=True)
            response = self._format_response(plan)
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            response = self._get_fallback_response(message)
        
        # Add assistant response to conversation
        self._add_message("assistant", response)
        
        return response

    def _add_message(self, role: str, content: str) -> None:
        """Add a message to the current conversation."""
        if not self._current_conversation:
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        }
        
        self._current_conversation.messages.append(message)
        self._current_conversation.last_updated = datetime.now()
        
        # Store in voice memory
        voice_memory.add_interaction(content, role)

    def _format_response(self, plan: Dict[str, Any]) -> str:
        """Format a plan into a natural-sounding response."""
        if "steps" in plan and plan["steps"]:
            first_step = plan["steps"][0]
            action = first_step.get("action", "")
            
            # Generate natural response based on action
            if action == "open":
                app = first_step.get("params", {}).get("app", "application")
                return f"Opening {app} now."
            elif action == "search":
                query = first_step.get("params", {}).get("query", "query")
                return f"Searching for {query}."
            elif action == "screenshot":
                return "Taking a screenshot now."
            else:
                return "I'll help you with that right away."
        
        return "I understand, let's get started."

    def _get_fallback_response(self, message: str) -> str:
        """Get a fallback response when LLM is unavailable."""
        message_lower = message.lower()
        
        if "open" in message_lower:
            return "Opening the requested application."
        elif "search" in message_lower:
            return "Searching for that now."
        elif "screenshot" in message_lower:
            return "Taking a screenshot."
        elif "stop" in message_lower:
            return "Stopping now."
        else:
            return "I'll help you with that."

    def get_conversation_history(self, conv_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the history of a conversation."""
        conversation = self._current_conversation
        if conv_id and conv_id in self._conversations:
            conversation = self._conversations[conv_id]
        
        if not conversation:
            return []
        
        return conversation.messages[-limit:]

    def clear_conversation(self) -> None:
        """Clear the current conversation."""
        self._current_conversation = None
        logger.info("Conversation cleared")


# Module-level singleton
conversation_manager = ConversationManager()

