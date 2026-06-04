
"""
jarvis_runtime.py
==================
Main entry point for JARVIS AI Operating System persistent runtime.
Integrates runtime_core, UI, and voice systems.
"""

import sys
import logging
import threading
import asyncio
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent / "logs" / "runtime_core_logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"jarvis_runtime_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log"

# Configure logging
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.encoding = 'utf-8'
file_handler = logging.FileHandler(str(log_file), encoding='utf-8')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)


def run_asyncio_runtime(loop):
    """Run asyncio runtime in a dedicated thread"""
    asyncio.set_event_loop(loop)
    from runtime.persistent_runtime import persistent_runtime
    loop.run_until_complete(persistent_runtime.run())


def run_legacy_runtime_in_thread():
    """Run JARVIS legacy runtime in a background thread (for compatibility)"""
    # Import runtime components here to avoid circular imports
    from runtime.runtime_manager import runtime_manager
    from runtime.hotkey_manager import hotkey_manager
    from integrations.speech_bridge.speech_listener import get_speech_listener
    from runtime.idle_controller import idle_controller
    from voice.text_to_speech import text_to_speech
    from runtime.event_bus import event_bus, EventType, Event

    # Parse command-line arguments
    enable_startup = "--startup" in sys.argv

    # Initialize runtime manager
    runtime_manager.initialize(enable_startup=enable_startup)

    # Hotkey manager now uses event bus
    def on_ctrl_p():
        from runtime.runtime_state_machine import runtime_state_machine, RuntimeState
        if runtime_state_machine.current_state != RuntimeState.PAUSED:
            event_bus.publish(Event(EventType.PAUSE, source="hotkey"))
        else:
            event_bus.publish(Event(EventType.RESUME, source="hotkey"))

    # Override hotkey callback temporarily to use event bus
    hotkey_manager.initialize()
    hotkey_manager.start()

    # Use our new integration layer's speech listener instead of the old one!
    speech_listener = get_speech_listener()
    speech_listener.start()
    idle_controller.start()

    # Speak startup greeting (MOVED TO MAIN QT THREAD VIA QTIMER)
    # try:
    #     logger.info("Playing startup greeting")
    #     text_to_speech.speak("JARVIS online. All systems initialized.")
    # except Exception as e:
    #     logger.warning(f"Failed to play startup greeting: {e}")

    # Start main runtime service
    try:
        runtime_manager.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received - shutting down")
        runtime_manager.shutdown()


def main():
    logger.info("=" * 70)
    logger.info("JARVIS AI Operating System - Persistent Runtime Starting")
    logger.info("=" * 70)

    # Import UI components
    from overlay.presence_manager import presence_manager
    from overlay.overlay_manager import overlay_manager
    from overlay.tray_manager import tray_manager
    from PyQt6.QtWidgets import QApplication

    # Create QApplication FIRST in the main thread
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Initialize UI components
    tray_manager.initialize()
    overlay_manager.initialize()
    presence_manager.initialize()

    # Start tray
    tray_manager.start()

    # Create and start asyncio loop in separate thread
    loop = asyncio.new_event_loop()
    asyncio_thread = threading.Thread(
        target=run_asyncio_runtime,
        args=(loop,),
        daemon=True,
        name="AsyncioRuntimeThread"
    )
    asyncio_thread.start()

    # Start legacy runtime in another thread
    runtime_thread = threading.Thread(
        target=run_legacy_runtime_in_thread,
        daemon=True,
        name="LegacyRuntimeThread"
    )
    runtime_thread.start()

    # Start overlay (now in main thread)
    overlay_manager.start_in_main_thread()
    
    # Function to play startup greeting in main Qt thread (safe)
    def play_startup_greeting():
        try:
            logger.info("Playing startup greeting (in main thread) - using DIRECT pyttsx3!")
            import pyttsx3
            engine = pyttsx3.init(driverName='sapi5')
            voices = engine.getProperty('voices')
            for v in voices:
                if "Microsoft David" in v.name:
                    engine.setProperty('voice', v.id)
            engine.setProperty('volume', 1.0)
            engine.setProperty('rate', 150)
            engine.say("JARVIS online! All systems initialized and ready!")
            logger.info("Calling engine.runAndWait()")
            engine.runAndWait()
            logger.info("TTS FINISHED SPEAKING (SUCCESS!)")
        except Exception as e:
            logger.error(f"ERROR speaking greeting: {e}", exc_info=True)

    # Use QTimer to call greeting after a short delay (in main thread)
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(1000, play_startup_greeting)

    # Run Qt event loop
    try:
        app.exec()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received - shutting down")
        from runtime.runtime_manager import runtime_manager
        runtime_manager.shutdown()


if __name__ == "__main__":
    main()
