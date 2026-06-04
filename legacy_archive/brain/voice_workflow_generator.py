
"""
voice_workflow_generator.py
===========================
Generates structured voice control workflows based on natural language input,
detected intent, and extracted requirements.
"""
from __future__ import annotations

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class VoiceAction:
    """Represents a single action in a voice workflow."""
    action_type: str
    params: Dict[str, Any]
    description: str


class VoiceWorkflowGenerator:
    """
    Generates structured voice control workflows (lists of VoiceAction)
    based on natural language input, detected intent, and extracted requirements.
    """

    def generate_from_input(
        self, user_input: str, category: str, requirements: List[str]
    ) -> List[VoiceAction]:
        """
        Main entry point to generate a voice workflow.
        """
        input_lower = user_input.lower()
        actions: List[VoiceAction] = []

        if category == "text_to_speech":
            # Check for test speaker command
            if "test speaker" in input_lower or "speaker test" in input_lower or "test speakers" in input_lower:
                actions.append(
                    VoiceAction(
                        action_type="speak",
                        params={"text": "This is a speaker test from JARVIS. If you can hear this, your speakers are working correctly."},
                        description="Run speaker test",
                    )
                )
            else:
                text = self._extract_text_to_speak(user_input)
                if text:
                    actions.append(
                        VoiceAction(
                            action_type="speak",
                            params={"text": text},
                            description=f"Speak: {text}",
                        )
                    )
        elif category == "speech_control":
            if "stop" in input_lower or "mute" in input_lower or "silence" in input_lower:
                actions.append(
                    VoiceAction(
                        action_type="stop_speaking",
                        params={},
                        description="Stop speaking",
                    )
                )
        elif category == "voice_interaction":
            # Check for voice profile switching
            profile_keywords = ["jarvis classic", "professional", "friendly", "technical", "cinematic"]
            for profile in profile_keywords:
                if profile in input_lower:
                    # Map to our profile names
                    profile_map = {
                        "jarvis classic": "jarvis_classic",
                        "professional": "professional",
                        "friendly": "friendly",
                        "technical": "technical",
                        "cinematic": "professional"  # Cinematic maps to professional for now
                    }
                    target_profile = profile_map.get(profile, "jarvis_classic")
                    actions.append(
                        VoiceAction(
                            action_type="set_profile",
                            params={"profile": target_profile},
                            description=f"Switch to {profile} voice profile",
                        )
                    )
                    break

            if any(trigger in input_lower for trigger in ["enable voice", "start listening", "activate microphone"]):
                actions.append(
                    VoiceAction(
                        action_type="enable_voice_mode",
                        params={},
                        description="Enable voice mode and start listening",
                    )
                )
            if "talk to me" in input_lower:
                actions.append(
                    VoiceAction(
                        action_type="start_conversation",
                        params={},
                        description="Start a conversational voice session",
                    )
                )

        return actions

    def _extract_text_to_speak(self, user_input: str) -> str:
        """Extract text to speak from input like "Speak hello world" or "Say welcome back Jarvis"."""
        # Check for common prefixes (case-insensitive)
        prefixes = ["speak", "say", "read aloud", "talk", "announce"]
        text_lower = user_input.lower()
        
        for prefix in sorted(prefixes, key=len, reverse=True):  # longer prefixes first
            prefix_len = len(prefix)
            if text_lower.startswith(prefix):
                # Extract everything after prefix
                extracted = user_input[prefix_len:].strip()
                if extracted:
                    return extracted
        
        # If no standard prefix, check for the word anywhere in the sentence and take the rest
        for prefix in prefixes:
            pos = text_lower.find(prefix)
            if pos != -1:
                start_pos = pos + len(prefix)
                extracted = user_input[start_pos:].strip()
                if extracted:
                    return extracted
        
        # Fallback: return whole input
        return user_input.strip()


# Module-level singleton
voice_workflow_generator = VoiceWorkflowGenerator()
