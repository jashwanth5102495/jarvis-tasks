
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis_runtime.logger import get_logger
from jarvis_runtime.runtime_state import get_state, set_state, RuntimeState
from jarvis_runtime.health_monitor import monitor_health
from jarvis_runtime.watchdog import run_watchdog
from jarvis_runtime.server_launcher import start_fastapi_server, stop_fastapi_server
from jarvis_runtime.tray_manager import start_tray, tray_stop_event, tray_available


logger = get_logger()


def main():
    logger.info("=== Jarvis AI Runtime Manager Starting ===")
    
    stop_event = threading.Event()
    
    try:
        start_tray()
        start_fastapi_server()
        
        health_thread = threading.Thread(target=monitor_health, args=(stop_event,), daemon=True)
        health_thread.start()
        
        watchdog_thread = threading.Thread(target=run_watchdog, args=(stop_event,), daemon=True)
        watchdog_thread.start()
        
        if tray_available:
            while not tray_stop_event.is_set():
                time.sleep(0.5)
        else:
            # If no tray, just wait for keyboard interrupt
            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal (KeyboardInterrupt)")
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal (KeyboardInterrupt)")
    finally:
        logger.info("Shutting down...")
        set_state(RuntimeState.SHUTTING_DOWN)
        stop_event.set()
        stop_fastapi_server()
        logger.info("=== Jarvis AI Runtime Manager Exited ===")


if __name__ == "__main__":
    main()
