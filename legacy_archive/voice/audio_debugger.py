
"""
audio_debugger.py
===============
Diagnostic tool for JARVIS audio/TTS system.
Lists audio devices, tests playback, validates TTS backend.
"""

import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def list_audio_devices():
    """List available audio output devices (using sounddevice if available)."""
    print("\n=== Available Audio Devices ===")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            print(f"  [{i}] {dev['name']} (output: {dev['max_output_channels'] > 0})")
        default = sd.default.device[1]
        print(f"\n  Default Output Device: [{default}] {devices[default]['name']}")
    except ImportError:
        print("  sounddevice not installed. Basic device listing unavailable.")
        print("  Note: TTS uses system default playback device.")


def test_tts_engine():
    """Test TTS engine initialization and playback."""
    print("\n=== Testing TTS Engine ===")
    try:
        from voice.text_to_speech import text_to_speech
        print("  TTS engine available.")
        test_text = "This is a speaker test from JARVIS."
        print(f"  Playing test: \"{test_text}\"")
        text_to_speech.speak(test_text)
        print("  Test playback complete!")
        return True
    except Exception as e:
        print(f"  TTS test FAILED: {e}")
        return False


def diagnose_audio_issues():
    """Run full audio diagnostics."""
    print("=" * 60)
    print("  JARVIS Audio Diagnostics Tool")
    print("=" * 60)
    list_audio_devices()
    test_tts_engine()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Configure basic logging for diagnostics
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    diagnose_audio_issues()

