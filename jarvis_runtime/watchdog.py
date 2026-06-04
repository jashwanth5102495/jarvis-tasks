
import time

from jarvis_runtime.logger import get_logger
from jarvis_runtime.runtime_state import get_state, set_state, RuntimeState
from jarvis_runtime.server_launcher import restart_fastapi_server


logger = get_logger()


def run_watchdog(stop_event) -> None:
    logger.info("Watchdog started")
    while not stop_event.is_set():
        time.sleep(1)
        
        state = get_state()
        if state == RuntimeState.RECOVERING:
            logger.info("Watchdog triggering server restart")
            restart_fastapi_server()
            set_state(RuntimeState.ACTIVE)
