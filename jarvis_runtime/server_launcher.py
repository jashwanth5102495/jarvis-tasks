
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from jarvis_runtime.logger import get_logger
from jarvis_runtime.runtime_state import get_state, set_state, RuntimeState


logger = get_logger()
server_process: Optional[subprocess.Popen] = None


def start_fastapi_server() -> None:
    global server_process
    logger.info("Starting FastAPI server...")
    set_state(RuntimeState.STARTING)
    
    project_root = Path(__file__).parent.parent
    server_script = project_root / "run_jarvis_server.py"
    
    try:
        server_process = subprocess.Popen(
            [sys.executable, str(server_script)],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"FastAPI server started with PID: {server_process.pid}")
        
        # Wait a bit for server to warm up
        time.sleep(3)
        set_state(RuntimeState.ACTIVE)
        
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
        set_state(RuntimeState.ERROR)


def stop_fastapi_server() -> None:
    global server_process
    if server_process and server_process.poll() is None:
        logger.info("Stopping FastAPI server...")
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
            logger.info("FastAPI server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}, forcing kill")
            server_process.kill()
        finally:
            server_process = None


def restart_fastapi_server() -> None:
    logger.info("Restarting FastAPI server...")
    stop_fastapi_server()
    time.sleep(2)
    start_fastapi_server()
