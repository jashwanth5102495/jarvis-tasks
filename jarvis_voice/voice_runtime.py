
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from jarvis_voice.microphone_manager import MicrophoneManager
from jarvis_voice.wakeword_engine import WakeWordEngine
from jarvis_voice.speech_listener import SpeechListener
from jarvis_voice.speech_transcriber import SpeechTranscriber
from jarvis_voice.command_processor import CommandProcessor


def main():
    print("[JARVIS] Starting voice runtime...")
    
    # Initialize components
    mic = MicrophoneManager()
    wakeword = WakeWordEngine()
    listener = SpeechListener()
    transcriber = SpeechTranscriber()
    processor = CommandProcessor()
    
    # Initialize wakeword and transcriber
    wakeword.initialize()
    transcriber.initialize()
    
    # Set callbacks
    def on_wakeword():
        listener.start_recording(on_recording_complete)
    
    def on_recording_complete(audio_data):
        transcript = transcriber.transcribe(audio_data)
        if transcript:
            command = processor.extract_command(transcript)
            processor.send_to_server(command)
    
    def on_audio(audio_data):
        if listener._recording:
            listener.add_audio(audio_data)
        else:
            wakeword.process(audio_data)
    
    wakeword.set_callback(on_wakeword)
    
    # Start microphone
    mic.start(on_audio)
    
    print("[JARVIS] Listening for wake word...")
    
    try:
        # Keep running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[JARVIS] Stopping...")
        mic.stop()
        wakeword.cleanup()


if __name__ == "__main__":
    main()
