
"""
manual_tts_test.py
===================
Simple interactive tool to test JARVIS's text-to-speech system.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO)

from jarvis.voice.text_to_speech import text_to_speech

def main():
    print("=" * 60)
    print("JARVIS Text-to-Speech Test")
    print("=" * 60)
    print("Enter text to speak, or 'quit' to exit.")
    print("-" * 60)

    try:
        while True:
            text = input("Enter text: ").strip()
            if text.lower() in ("quit", "exit", "q"):
                print("Exiting test.")
                break
            if text:
                text_to_speech.speak(text)
    except KeyboardInterrupt:
        print("\nExiting test.")


if __name__ == "__main__":
    main()

