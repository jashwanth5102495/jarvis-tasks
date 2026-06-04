
"""
wake_listener.py
================
Wake-word listener integration for JARVIS runtime with real STT!
Listens for "Hey Jarvis" when active, then captures command!
"""

import logging
import threading
from typing import Optional

from jarvis.runtime.event_bus import event_bus, EventType, Event
from jarvis.runtime.runtime_state_machine import runtime_state_machine, RuntimeState

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Force debug logging for wake listener!

class WakeListener:
    def __init__(self):
        self._running: bool = False
        self._listener_thread: Optional[threading.Thread] = None
        self._recognizer = None
        self._microphone = None

    def initialize(self) -> None:
        logger.info("Initializing wake listener")
        try:
            import speech_recognition as sr
            logger.info(f"SpeechRecognition version: {sr.__version__}")
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 200  # Lower threshold to pick up more!
            self._recognizer.pause_threshold = 0.5
            self._recognizer.dynamic_energy_threshold = False  # Disable dynamic adjustment!
            self._microphone = sr.Microphone()
            logger.info("Speech recognition and microphone initialized successfully")
            logger.info(f"Fixed energy threshold set to: {self._recognizer.energy_threshold}")
        except ImportError as e:
            logger.error(f"SpeechRecognition not available: {e}")
        except Exception as e:
            logger.error(f"Error initializing microphone: {e}", exc_info=True)

    def _listen_loop(self) -> None:
        logger.info("Wake listener started (active)")
        import speech_recognition as sr
        while self._running:
            if runtime_state_machine.current_state == RuntimeState.PAUSED:
                import time
                time.sleep(0.5)
                continue

            # Listen for wake word
            try:
                logger.debug("Listening for wake word...")
                with self._microphone as source:
                    audio = self._recognizer.listen(source, phrase_time_limit=3)
                
                # Recognize wake word
                text = self._recognizer.recognize_google(audio).lower()
                logger.info(f"Heard: {text}")

                if any(phrase in text for phrase in ["hey jarvis", "okay jarvis", "jarvis"]):
                    logger.info("Wake word detected!")
                    event_bus.publish(Event(EventType.WAKE_WORD_DETECTED, source="wake_listener"))
                    runtime_state_machine.transition_to(RuntimeState.LISTENING)
                    self._capture_command()
            except sr.UnknownValueError:
                # Didn't understand, keep listening
                logger.debug("Could not understand audio")
                continue
            except sr.RequestError as e:
                logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            except Exception as e:
                logger.error(f"Wake listener error: {e}", exc_info=True)
        logger.info("Wake listener stopped")

    def _capture_command(self) -> None:
        try:
            import speech_recognition as sr
            logger.info("Capturing command...")
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self._recognizer.listen(source, phrase_time_limit=5)
            command = self._recognizer.recognize_google(audio).lower()
            logger.info(f"Command received: {command}")
            
            # Publish command event
            event_bus.publish(Event(EventType.COMMAND_RECEIVED, data=command, source="wake_listener"))
            
            # Transition to thinking state
            runtime_state_machine.transition_to(RuntimeState.THINKING)
            
            # Process command
            self._process_command(command)
        except sr.UnknownValueError:
            logger.warning("Could not understand command")
            runtime_state_machine.transition_to(RuntimeState.IDLE)
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            runtime_state_machine.transition_to(RuntimeState.IDLE)
        except Exception as e:
            logger.error(f"Command capture error: {e}", exc_info=True)
            runtime_state_machine.transition_to(RuntimeState.IDLE)

    def _process_command(self, command: str) -> None:
        try:
            from jarvis.core.brain import brain
            from jarvis.core.planner import planner
            from jarvis.core.skills import skill_registry
            from jarvis.core.memory_manager import memory_system
            from jarvis.core.models import MemoryRecord

            logger.info(f"Task received: {command}")
            goal = brain.analyze_task(command)

            # Update state to THINKING
            runtime_state_machine.transition_to(RuntimeState.THINKING)
            event_bus.publish(Event(EventType.THINKING_STARTED, data=goal, source="wake_listener"))

            # Internal commands (debug toggle, etc.)
            if goal.category == "internal_commands":
                logger.info("Internal command executed")
                runtime_state_machine.transition_to(RuntimeState.IDLE)
                return

            # Unknown intent
            if goal.category == "unknown":
                logger.warning("Unknown command category")
                from jarvis.voice.text_to_speech import text_to_speech
                text_to_speech.speak("I'm sorry, I didn't understand that.")
                runtime_state_machine.transition_to(RuntimeState.IDLE)
                return

            # Plan
            plan = planner.create_plan(goal)
            suggested_skills = skill_registry.recommend_skills(
                goal.category, goal.goal
            )

            # Save to memory
            record = MemoryRecord(
                task=command,
                goal=goal,
                plan=plan,
                suggested_skills=suggested_skills,
            )
            memory_system.save_task(record)

            # Execute
            runtime_state_machine.transition_to(RuntimeState.EXECUTING)
            event_bus.publish(Event(EventType.EXECUTION_STARTED, data=command, source="wake_listener"))
            logger.info("Executing plan...")
            if goal.category == "computer_control":
                from jarvis.computer_control.control_workflow_generator import control_workflow_generator
                from jarvis.computer_control.control_manager import control_manager
                control_actions = control_workflow_generator.generate_from_input(
                    command, goal.category, goal.requirements
                )
                if control_actions:
                    control_manager.execute_actions(
                        control_actions, goal=goal.goal
                    )
            elif goal.category in ["text_to_speech", "speech_control", "voice_interaction"]:
                from jarvis.core.voice_workflow_generator import voice_workflow_generator
                from jarvis.execution.execution_engine import execution_manager
                voice_actions = voice_workflow_generator.generate_from_input(
                    command, goal.category, goal.requirements
                )
                if voice_actions:
                    from jarvis.execution.task_router import task_router
                    execution_steps = task_router.route(goal)
                    result = execution_manager.execute(goal)
            else:
                from jarvis.core.orchestrator import workflow_orchestrator
                workflow_orchestrator.run(goal)

            # Speak response
            logger.info("Command execution complete")
            from jarvis.voice.text_to_speech import text_to_speech
            response = f"Task completed: {command}"
            runtime_state_machine.transition_to(RuntimeState.SPEAKING)
            event_bus.publish(Event(EventType.SPEAK_START, data=response, source="wake_listener"))
            text_to_speech.speak(response)
            event_bus.publish(Event(EventType.SPEAK_END, source="wake_listener"))

            # Return to idle
            runtime_state_machine.transition_to(RuntimeState.IDLE)
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            runtime_state_machine.transition_to(RuntimeState.ERROR)
            from jarvis.voice.text_to_speech import text_to_speech
            text_to_speech.speak(f"Sorry, I encountered an error: {e}")
            runtime_state_machine.transition_to(RuntimeState.IDLE)

    def start(self) -> None:
        if self._listener_thread and self._listener_thread.is_alive():
            return
        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="WakeListener"
        )
        self._listener_thread.start()

    def stop(self) -> None:
        logger.info("Stopping wake listener")
        self._running = False


# Module-level singleton
wake_listener = WakeListener()

