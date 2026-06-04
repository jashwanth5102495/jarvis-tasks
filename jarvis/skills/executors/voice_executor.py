
"""
voice_executor.py
==================
Executor for voice-related actions (speaking, listening, etc.)
"""
from __future__ import annotations

import logging

from jarvis.voice.voice_manager import voice_manager
from jarvis.skills.base import BaseExecutor
from jarvis.execution.execution_context import ExecutionContext, RiskLevel

logger = logging.getLogger(__name__)


class VoiceExecutor(BaseExecutor):
    """Executor for voice actions."""

    SUPPORTED_ACTIONS = [
        "speak",
        "stop_speaking",
        "enable_voice_mode",
        "start_conversation",
        "set_profile",
    ]

    ACTION_RISK_MAP = {
        "speak": RiskLevel.LOW,
        "stop_speaking": RiskLevel.LOW,
        "enable_voice_mode": RiskLevel.MEDIUM,
        "start_conversation": RiskLevel.MEDIUM,
        "set_profile": RiskLevel.LOW,
    }

    def _action_speak(self, ctx: ExecutionContext) -> str:
        """Speak a text string using the voice manager's TTS."""
        text = ctx.params.get("text", "")
        logger.info(f"VoiceExecutor: Speaking text: {text}")
        voice_manager.speak(text)
        return f"Spoken: {text}"

    def _action_stop_speaking(self, ctx: ExecutionContext) -> str:
        """Stop any ongoing audio playback."""
        logger.info("VoiceExecutor: Stopping speaking")
        voice_manager._on_interruption("User requested stop")
        return "Stopped speaking"

    def _action_enable_voice_mode(self, ctx: ExecutionContext) -> str:
        """Start the voice manager and enable wake word detection."""
        logger.info("VoiceExecutor: Enabling voice mode")
        if not voice_manager.state.is_listening:
            voice_manager.start()
        return "Voice mode enabled and listening"

    def _action_start_conversation(self, ctx: ExecutionContext) -> str:
        """Start a conversational voice session."""
        logger.info("VoiceExecutor: Starting conversation")
        if not voice_manager.state.is_listening:
            voice_manager.start()
        voice_manager.speak("I'm ready to talk. What can I do for you?")
        return "Conversation started"

    def _action_set_profile(self, ctx: ExecutionContext) -> str:
        """Switch to a different voice profile."""
        profile_name = ctx.params.get("profile", "jarvis_classic")
        logger.info(f"VoiceExecutor: Switching to profile: {profile_name}")
        from jarvis.voice.text_to_speech import text_to_speech
        text_to_speech.set_profile(profile_name)
        voice_manager.speak(f"Voice profile set to {profile_name}.")
        return f"Switched to voice profile: {profile_name}"


# Module-level singleton
voice_executor = VoiceExecutor()
