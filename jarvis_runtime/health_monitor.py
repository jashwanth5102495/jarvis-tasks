
import time
import requests
from typing import Optional

from jarvis_runtime.logger import get_logger
from jarvis_runtime.runtime_state import get_state, set_state, RuntimeState


logger = get_logger()
HEALTH_URL = "http://localhost:5000/health"


def is_server_healthy() -> bool:
    try:
        response = requests.get(HEALTH_URL, timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "online"
        return False
    except Exception as e:
        logger.debug(f"Health check failed: {e}")
        return False


def monitor_health(stop_event) -> None:
    logger.info("Health monitor started")
    last_known_good = time.time()
    
    while not stop_event.is_set():
        current_state = get_state()
        if current_state in (RuntimeState.SHUTTING_DOWN, RuntimeState.PAUSED):
            time.sleep(1)
            continue
        
        healthy = is_server_healthy()
        
        if healthy:
            last_known_good = time.time()
            if current_state != RuntimeState.ACTIVE:
                set_state(RuntimeState.ACTIVE)
        else:
            time_since_good = time.time() - last_known_good
            if time_since_good > 5:
                logger.warning("Health check failed repeatedly - triggering recovery")
                set_state(RuntimeState.RECOVERING)
        
        time.sleep(1)
