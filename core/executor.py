
from jarvis_server.core.command_router import route_command


def execute_command(command: str) -> tuple[bool, str]:
    print(f"[JARVIS] Command received: {command}")
    print("[JARVIS] Executing...")
    success, message = route_command(command)
    print("[JARVIS] Completed.")
    return success, message
