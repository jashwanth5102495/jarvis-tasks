
"""
Speech listener module - handles microphone capture, wake word detection, and command transcription.
Integrates with our AI OS runtime's event bus and state machine!
"""
import logging
import threading
import time
from typing import Optional

# Use SpeechRecognition for microphone capture and basic STT
import speech_recognition as sr

from runtime.event_bus import event_bus, EventType, Event
from runtime.runtime_state_machine import runtime_state_machine, RuntimeState

logger = logging.getLogger(__name__)


class SpeechListener:
    """
    Continuous speech listener that detects wake words and captures commands!
    """

    def __init__(
        self,
        wake_words: list[str] = ["hey jarvis", "okay jarvis", "jarvis"],
        phrase_time_limit: float = 3.0,
        command_phrase_time_limit: float = 5.0,
    ):
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None

        self.wake_words = [word.lower() for word in wake_words]
        self.phrase_time_limit = phrase_time_limit
        self.command_phrase_time_limit = command_phrase_time_limit

        # Initialize recognizer and microphone
        self._recognizer = sr.Recognizer()
        self._recognizer.dynamic_energy_threshold = False
        self._recognizer.energy_threshold = 200  # Sensitivity (adjust as needed)
        self._recognizer.pause_threshold = 0.5

        try:
            self._microphone = sr.Microphone()
            logger.info("Microphone initialized successfully!")
            # Adjust for ambient noise
            with self._microphone as source:
                logger.info("Adjusting for ambient noise...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info(f"Energy threshold set to: {self._recognizer.energy_threshold}")
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}", exc_info=True)
            raise

    def _listen_loop(self):
        """Main listener loop that runs in a separate thread!"""
        logger.info("Speech listener started!")

        while self._running:
            try:
                if runtime_state_machine.current_state == RuntimeState.PAUSED:
                    time.sleep(0.5)
                    continue

                # Listen for wake word
                logger.debug("Listening for wake word...")
                with self._microphone as source:
                    audio = self._recognizer.listen(source, phrase_time_limit=self.phrase_time_limit)

                # Try to recognize
                try:
                    text = self._recognizer.recognize_google(audio).lower()
                    logger.debug(f"Heard: {text}")
                    if any(word in text for word in self.wake_words):
                        self._handle_wake_detected()
                except sr.UnknownValueError:
                    logger.debug("Didn't understand wake word")
                except sr.RequestError as e:
                    logger.error(f"Speech recognition service error: {e}")

            except Exception as e:
                logger.error(f"Error in listener loop: {e}", exc_info=True)
                time.sleep(1)

        logger.info("Speech listener stopped!")

    def _handle_wake_detected(self):
        """Wake word detected! Now capture command!"""
        logger.info("Wake word detected!")

        # Publish event and update state
        event_bus.publish(Event(EventType.WAKE_WORD_DETECTED, source="speech_listener"))
        runtime_state_machine.transition_to(RuntimeState.LISTENING)

        try:
            # Capture command
            logger.info("Listening for command...")
            with self._microphone as source:
                audio = self._recognizer.listen(source, phrase_time_limit=self.command_phrase_time_limit)

            command_text = self._recognizer.recognize_google(audio)
            logger.info(f"Command captured: {command_text}")

            # Publish command received event
            event_bus.publish(
                Event(
                    EventType.COMMAND_RECEIVED,
                    data=command_text,
                    source="speech_listener",
                )
            )
            runtime_state_machine.transition_to(RuntimeState.THINKING)

            # Process command using our existing pipeline
            self._process_command(command_text)

        except sr.UnknownValueError:
            logger.warning("Didn't understand command")
            runtime_state_machine.transition_to(RuntimeState.IDLE)
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            runtime_state_machine.transition_to(RuntimeState.IDLE)
        except Exception as e:
            logger.error(f"Error capturing command: {e}", exc_info=True)
            runtime_state_machine.transition_to(RuntimeState.IDLE)

    def _process_command(self, command: str):
        """Process command using our existing pipeline! (Copied from main.py)"""
        try:
            from core.brain import brain
            from core.planner import planner
            from core.skills import skill_registry
            from core.memory import memory_system
            from core.models import MemoryRecord
            from voice.text_to_speech import text_to_speech

            runtime_state_machine.transition_to(RuntimeState.EXECUTING)
            event_bus.publish(
                Event(
                    EventType.EXECUTION_STARTED,
                    data=command,
                    source="speech_listener",
                )
            )

            logger.info(f"Brain analyzing command: {command}")
            goal = brain.analyze_task(command)

            if goal.category == "internal_commands":
                logger.info("Internal command executed")
                runtime_state_machine.transition_to(RuntimeState.IDLE)
                return

            if goal.category == "unknown":
                logger.warning("Unknown command category")
                text_to_speech.speak("I'm sorry, I didn't understand that.")
                runtime_state_machine.transition_to(RuntimeState.IDLE)
                return

            plan = planner.create_plan(goal)
            suggested_skills = skill_registry.recommend_skills(goal.category, goal.goal)
            record = MemoryRecord(task=command, goal=goal, plan=plan, suggested_skills=suggested_skills)
            memory_system.save_task(record)

            if goal.category == "computer_control":
                from computer_control.control_workflow_generator import control_workflow_generator
                from computer_control.control_manager import control_manager
                control_actions = control_workflow_generator.generate_from_input(command, goal.category, goal.requirements)
                if control_actions:
                    control_manager.execute_actions(control_actions, goal=goal.goal)
            elif goal.category in ["text_to_speech", "speech_control", "voice_interaction"]:
                from brain.voice_workflow_generator import voice_workflow_generator
                from execution.manager import execution_manager
                voice_actions = voice_workflow_generator.generate_from_input(command, goal.category, goal.requirements)
                if voice_actions:
                    from execution.task_router import task_router
                    execution_steps = task_router.route(goal)
                    execution_manager.execute(goal)
            else:
                from core.workflow_orchestrator import workflow_orchestrator
                workflow_orchestrator.run(goal)

            logger.info("Command execution complete!")
            runtime_state_machine.transition_to(RuntimeState.SPEAKING)
            response = f"Command executed: {command}"
            event_bus.publish(Event(EventType.SPEAK_START, data=response, source="speech_listener"))
            text_to_speech.speak(response)
            event_bus.publish(Event(EventType.SPEAK_END, source="speech_listener"))
            runtime_state_machine.transition_to(RuntimeState.IDLE)

        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            runtime_state_machine.transition_to(RuntimeState.ERROR)
            from voice.text_to_speech import text_to_speech
            text_to_speech.speak(f"Sorry, I encountered an error.")
            runtime_state_machine.transition_to(RuntimeState.IDLE)

    def start(self):
        if self._listener_thread and self._listener_thread.is_alive():
            logger.warning("Listener already running!")
            return
        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="SpeechListener",
        )
        self._listener_thread.start()

    def stop(self):
        logger.info("Stopping speech listener...")
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=5)


# Module singleton!
_speech_listener: Optional[SpeechListener] = None


def get_speech_listener() -> SpeechListener:
    global _speech_listener
    if _speech_listener is None:
        _speech_listener = SpeechListener()
    return _speech_listener
