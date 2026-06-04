
import pyttsx3

_engine = None


def get_tts_engine():
    global _engine
    if not _engine:
        _engine = pyttsx3.init()
    return _engine


def speak(text: str) -> None:
    print(f"[JARVIS] Speaking: {text}")
    try:
        engine = get_tts_engine()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[JARVIS] TTS Error: {e}")
