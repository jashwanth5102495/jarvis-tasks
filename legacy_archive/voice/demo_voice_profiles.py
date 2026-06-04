
"""
demo_voice_profiles.py
=======================
Interactive demo of JARVIS voice profiles and TTS engines.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO)

from voice.text_to_speech import text_to_speech
from voice.voice_profile_manager import voice_profile_manager


def main():
    print("=" * 60)
    print("JARVIS Voice Profile Demo")
    print("=" * 60)
    print()

    # List available profiles
    print("Available Voice Profiles:")
    for i, name in enumerate(voice_profile_manager.list_profiles(), start=1):
        print(f"  {i}. {name}")
    print()

    # Test each profile
    test_text = "Hello, I'm JARVIS. How may I assist you today?"
    for name in voice_profile_manager.list_profiles():
        print("-" * 60)
        print(f"Testing profile: {name}")
        print("-" * 60)
        text_to_speech.set_profile(name)
        text_to_speech.speak(test_text)
        print()

    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

