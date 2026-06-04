
"""
test_tts_audio_output.py
=========================
Test suite for JARVIS's text-to-speech audio output system.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice.text_to_speech import text_to_speech
from brain.voice_workflow_generator import voice_workflow_generator
from brain.categories import CATEGORIES
from core.models import Goal


def test_tts_initialization():
    print("[OK] Test 1: TTS engine initialization")
    assert text_to_speech is not None
    assert text_to_speech.config is not None


def test_speak_command_classification():
    print("[OK] Test 2: Speak command processing")
    goal = Goal(
        goal="Speak hello world",
        category="text_to_speech",
        requirements=[],
        confidence=0.95
    )
    actions = voice_workflow_generator.generate_from_input(
        goal.goal,
        goal.category,
        goal.requirements
    )
    assert len(actions) == 1
    assert actions[0].action_type == "speak"
    assert "hello world" in actions[0].params["text"].lower()


def test_speaker_test():
    print("[OK] Test 3: Speaker test command")
    goal = Goal(
        goal="Test speaker",
        category="text_to_speech",
        requirements=[],
        confidence=0.95
    )
    actions = voice_workflow_generator.generate_from_input(
        goal.goal,
        goal.category,
        goal.requirements
    )
    assert len(actions) == 1
    assert "speaker test" in actions[0].params["text"].lower()


def test_speak():
    print("[OK] Test 4: Speaking test text")
    text_to_speech.speak("This is a test of JARVIS's text-to-speech system.")


if __name__ == "__main__":
    print("=" * 60)
    print("JARVIS TTS Audio Output Tests")
    print("=" * 60)
    test_tts_initialization()
    test_speak_command_classification()
    test_speaker_test()
    print("\n[OK] All non-auditory tests passed!")
    print("\nRunning auditory test (you should hear speech):")
    test_speak()
    print("[OK] Auditory test complete!")

