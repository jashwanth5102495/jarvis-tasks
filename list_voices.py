
import pyttsx3

engine = pyttsx3.init()

voices = engine.getProperty('voices')
print(f"Found {len(voices)} voices:")
for i, voice in enumerate(voices):
    print(f"Voice {i}:")
    print(f"  ID: {voice.id}")
    print(f"  Name: {voice.name}")
    print(f"  Languages: {voice.languages}")
    print(f"  Gender: {voice.gender}")
    print(f"  Age: {voice.age}")
    print()

# Test normal speed (150 WPM)
print("Testing voice at 150 WPM...")
engine.setProperty('rate', 150)
engine.say("Hello! This is a test of the text to speech system at a normal speed.")
engine.runAndWait()
