
"""
STANDALONE VOICE TEST - NO JARVIS RUNTIME!
Just tests pyttsx3 speaking!
"""
import sys

print("IMPORTING pyttsx3...")
try:
    import pyttsx3
    print("pyttsx3 imported successfully!")
except Exception as e:
    print(f"ERROR IMPORTING pyttsx3: {e}")
    sys.exit(1)


print("INITIALIZING TTS ENGINE...")
try:
    engine = pyttsx3.init(driverName='sapi5')
    print("Engine initialized!")
    voices = engine.getProperty('voices')
    print(f"Available voices: {len(voices)}")
    for i, v in enumerate(voices):
        print(f"  Voice {i}: {v.name}")
    # Try to set Microsoft David Desktop if available
    target_voice = None
    for v in voices:
        if "Microsoft David" in v.name or "David" in v.name:
            target_voice = v.id
            print(f"Target voice found: {v.name}")
            break
    if target_voice:
        engine.setProperty('voice', target_voice)
    engine.setProperty('volume', 1.0)  # Max volume
    engine.setProperty('rate', 150)    # Normal speed
    print("Engine configured!")
    
    print("SPEAKING NOW...")
    engine.say("Hello! I am Jarvis. Testing voice system!")
    engine.runAndWait()
    print("SPEAKING COMPLETE!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
