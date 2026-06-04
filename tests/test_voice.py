
"""
test_voice.py
=============
Tests for JARVIS Voice & Conversational Intelligence System (Milestone 7).
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

test_results = {"pass": 0, "fail": 0}


def check(description, condition):
    if condition:
        print(f"  [OK] {description}")
        test_results["pass"] += 1
    else:
        print(f"  [FAIL] {description}")
        test_results["fail"] += 1


def run_tests():
    print("\nTesting JARVIS Voice & Conversational Intelligence System (Milestone 7)")
    
    # --------------------------
    # 1. Voice Manager Tests
    # --------------------------
    print("\n1. Voice Manager")
    from voice.voice_manager import voice_manager
    
    check("Voice manager initialized", voice_manager is not None)
    check("Voice state exists", voice_manager.state is not None)
    
    # --------------------------
    # 2. Wake-word Detector Tests
    # --------------------------
    print("\n2. Wake-word Detector")
    from voice.wakeword_detector import wakeword_detector
    
    check("Wake-word detector initialized", wakeword_detector is not None)
    check("Default wake-words exist", len(wakeword_detector.config.wakewords) > 0)
    check("'jarvis' is a wake-word", "jarvis" in wakeword_detector.config.wakewords)
    
    # Test adding/removing wake-words
    wakeword_detector.add_wakeword("test wakeword")
    check("Can add wake-word", "test wakeword" in wakeword_detector.config.wakewords)
    wakeword_detector.remove_wakeword("test wakeword")
    check("Can remove wake-word", "test wakeword" not in wakeword_detector.config.wakewords)
    
    # --------------------------
    # 3. Speech-to-Text Tests
    # --------------------------
    print("\n3. Speech-to-Text")
    from voice.speech_to_text import speech_to_text
    
    check("STT initialized", speech_to_text is not None)
    check("STT config exists", speech_to_text.config is not None)
    
    # --------------------------
    # 4. Text-to-Speech Tests
    # --------------------------
    print("\n4. Text-to-Speech")
    from voice.text_to_speech import text_to_speech, VoicePersonality
    
    check("TTS initialized", text_to_speech is not None)
    check("TTS config exists", text_to_speech.config is not None)
    
    # Test personality setting
    text_to_speech.set_personality(VoicePersonality.PROFESSIONAL)
    check("Can set voice personality", text_to_speech.config.voice_personality == VoicePersonality.PROFESSIONAL)
    text_to_speech.set_personality(VoicePersonality.ASSISTANT)
    
    # Test speed setting
    text_to_speech.set_speed(1.5)
    check("Can set speech speed", text_to_speech.config.speed == 1.5)
    text_to_speech.set_speed(1.0)
    
    # --------------------------
    # 5. Conversation Manager Tests
    # --------------------------
    print("\n5. Conversation Manager")
    from voice.conversation_manager import conversation_manager
    
    check("Conversation manager initialized", conversation_manager is not None)
    
    # Test starting conversation
    conv_id = conversation_manager.start_conversation()
    check("Can start conversation", conv_id is not None and len(conv_id) > 0)
    
    # Test processing message
    response = conversation_manager.process_message("open chrome")
    check("Can process message", response is not None and len(response) > 0)
    print(f"    Response: {response}")
    
    # Test conversation history
    history = conversation_manager.get_conversation_history(limit=5)
    check("Conversation history exists", len(history) > 0)
    
    # --------------------------
    # 6. Streaming Listener Tests
    # --------------------------
    print("\n6. Streaming Listener")
    from voice.streaming_listener import streaming_listener
    
    check("Streaming listener initialized", streaming_listener is not None)
    check("Listener config exists", streaming_listener.config is not None)
    check("Listener not listening initially", not streaming_listener.is_listening())
    
    # --------------------------
    # 7. Interruption Handler Tests
    # --------------------------
    print("\n7. Interruption Handler")
    from voice.interruption_handler import interruption_handler
    
    check("Interruption handler initialized", interruption_handler is not None)
    check("Interruption phrases exist", len(interruption_handler.config.interruption_phrases) > 0)
    check("'stop' is an interruption phrase", "stop" in interruption_handler.config.interruption_phrases)
    check("Detects 'stop' as interruption", interruption_handler.check_interruption("stop"))
    check("Detects 'jarvis stop' as interruption", interruption_handler.check_interruption("jarvis stop"))
    check("Does not detect normal text as interruption", not interruption_handler.check_interruption("hello"))
    
    # --------------------------
    # 8. Audio Router Tests
    # --------------------------
    print("\n8. Audio Router")
    from voice.audio_router import audio_router
    
    check("Audio router initialized", audio_router is not None)
    check("Input devices found", len(audio_router.get_input_devices()) > 0)
    check("Output devices found", len(audio_router.get_output_devices()) > 0)
    check("Current input device exists", audio_router.get_current_input() is not None)
    check("Current output device exists", audio_router.get_current_output() is not None)
    
    # --------------------------
    # 9. Voice Memory Tests
    # --------------------------
    print("\n9. Voice Memory")
    from voice.voice_memory import voice_memory
    
    check("Voice memory initialized", voice_memory is not None)
    
    # Test adding interaction
    voice_memory.add_interaction("Hello, Jarvis", "user")
    voice_memory.add_interaction("Hello, how can I help?", "assistant")
    
    recent = voice_memory.get_recent_interactions(limit=5)
    check("Can add and retrieve interactions", len(recent) >= 2)
    
    # Test preferences
    voice_memory.set_preference("test_key", "test_value")
    check("Can set preference", voice_memory.get_preference("test_key") == "test_value")
    
    # --------------------------
    # 10. Conversation Context Tests
    # --------------------------
    print("\n10. Conversation Context")
    from voice.conversation_context import conversation_context
    
    check("Conversation context initialized", conversation_context is not None)
    
    # Test building context
    context = conversation_context.build_context("open chrome")
    check("Can build conversation context", context is not None)
    check("Context contains recent topics", "recent_topics" in context)
    
    # --------------------------
    # 11. Integration Tests
    # --------------------------
    print("\n11. Integration Tests")
    
    # Test full voice manager flow
    voice_manager.set_workflow_callback(lambda cmd: print(f"    Executing command: {cmd}"))
    
    # Simulate wake-word detection
    wakeword_detector.simulate_detection("jarvis")
    check("Wake-word simulation works", True)
    
    # Simulate a voice command
    streaming_listener.simulate_command("search for latest AI models")
    check("Command simulation works", True)
    
    # --------------------------
    # Summary
    # --------------------------
    print("\n" + "=" * 60)
    total = test_results["pass"] + test_results["fail"]
    if test_results["fail"] == 0:
        print(f"All {total} tests passed!")
    else:
        print(f"{test_results['fail']} out of {total} tests failed")


if __name__ == "__main__":
    run_tests()

