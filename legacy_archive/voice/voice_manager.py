
"""
voice_manager.py
===============
Main voice manager that orchestrates all voice interactions for JARVIS.
Coordinates wake-word detection, speech-to-text, conversation management,
text-to-speech, and interruption handling.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from voice.wakeword_detector import wakeword_detector
from voice.speech_to_text import speech_to_text
from voice.text_to_speech import text_to_speech
from voice.conversation_manager import conversation_manager
from voice.streaming_listener import streaming_listener
from voice.interruption_handler import interruption_handler
from voice.audio_router import audio_router
from voice.voice_memory import voice_memory
from voice.conversation_context import conversation_context

logger = logging.getLogger(__name__)


@dataclass
class VoiceState:
    """Current state of the voice system."""
    is_listening: bool = False
    is_speaking: bool = False
    wakeword_detected: bool = False
    conversation_active: bool = False
    current_conversation_id: Optional[str] = None
    last_interaction: Optional[datetime] = None


class VoiceManager:
    """
    Main manager for all voice interactions.
    Coordinates wake-word detection, STT, TTS, conversation management,
    and workflow execution through voice commands.
    """

    def __init__(self):
        self.state = VoiceState()
        self._listening_thread: Optional[threading.Thread] = None
        self._should_run: bool = False
        self._workflow_callback: Optional[Callable[[str], None]] = None

    def set_workflow_callback(self, callback: Callable[[str], None]) -> None:
        """Set a callback to execute when a voice command is received."""
        self._workflow_callback = callback

    def start(self) -> None:
        """Start the voice system."""
        if self._should_run:
            logger.warning("Voice system already running")
            return
        
        self._should_run = True
        logger.info("Starting JARVIS voice system")
        
        # Start wake-word detector
        wakeword_detector.set_wakeword_callback(self._on_wakeword_detected)
        wakeword_detector.start()
        
        # Start streaming listener
        streaming_listener.set_transcription_callback(self._on_transcription)
        
        # Set up interruption handler
        interruption_handler.set_interruption_callback(self._on_interruption)
        
        self.state.is_listening = True
        self._listening_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._listening_thread.start()
        
        logger.info("Voice system started successfully")

    def stop(self) -> None:
        """Stop the voice system."""
        self._should_run = False
        self.state.is_listening = False
        wakeword_detector.stop()
        streaming_listener.stop()
        
        if self._listening_thread and self._listening_thread.is_alive():
            self._listening_thread.join(timeout=2.0)
        
        logger.info("Voice system stopped")

    def _run_loop(self) -> None:
        """Main loop for the voice system."""
        while self._should_run:
            try:
                # Check for state updates
                pass
            except Exception as e:
                logger.error(f"Error in voice system loop: {e}")

    def _on_wakeword_detected(self, wakeword: str) -> None:
        """Handle wake-word detection."""
        logger.info(f"Wake-word detected: {wakeword}")
        self.state.wakeword_detected = True
        self.state.conversation_active = True
        
        # Start listening for command
        streaming_listener.start_listening()
        
        # Speak confirmation
        text_to_speech.speak("Yes, how can I help you?")

    def _on_transcription(self, text: str) -> None:
        """Handle speech-to-text transcription."""
        if not text.strip():
            return
        
        logger.info(f"Transcribed: {text}")
        self.state.last_interaction = datetime.now()
        
        # Check for interruption commands
        if interruption_handler.check_interruption(text):
            return
        
        # Process the command
        self._process_command(text)

    def _process_command(self, text: str) -> None:
        """Process a voice command."""
        # Store in voice memory
        voice_memory.add_interaction(text, "user")
        
        # Build conversation context
        context = conversation_context.build_context(text)
        
        # Get response from conversation manager
        response = conversation_manager.process_message(text, context)
        
        # Speak response
        if response:
            text_to_speech.speak(response)
            voice_memory.add_interaction(response, "assistant")
        
        # Execute workflow if needed
        if self._workflow_callback:
            self._workflow_callback(text)

    def _on_interruption(self, reason: str) -> None:
        """Handle an interruption."""
        logger.info(f"Interruption detected: {reason}")
        self.state.is_speaking = False
        text_to_speech.stop()
        streaming_listener.stop_listening()

    def speak(self, text: str) -> None:
        """Speak text using TTS."""
        self.state.is_speaking = True
        text_to_speech.speak(text)
        voice_memory.add_interaction(text, "assistant")
        self.state.is_speaking = False

    def get_conversation_history(self, limit: int = 10) -> list:
        """Get recent conversation history."""
        return voice_memory.get_recent_interactions(limit)


# Module-level singleton
voice_manager = VoiceManager()

