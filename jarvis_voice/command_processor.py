
import requests
from .config import Config


class CommandProcessor:
    def __init__(self):
        self.server_url = Config.JARVIS_SERVER_URL

    def extract_command(self, transcript: str) -> str:
        """Extract command by removing wake word."""
        transcript_lower = transcript.lower()
        wake_word = Config.WAKE_WORD.lower()
        
        # Remove wake word from the beginning
        if transcript_lower.startswith(wake_word):
            command = transcript[len(wake_word):].strip()
        else:
            # Try to find wake word anywhere
            wake_word_index = transcript_lower.find(wake_word)
            if wake_word_index != -1:
                command = transcript[wake_word_index + len(wake_word):].strip()
            else:
                command = transcript.strip()
        
        return command

    def send_to_server(self, command: str) -> bool:
        """Send command to Jarvis server."""
        if not command:
            return False

        print(f"[JARVIS] Command: {command}")
        print("[JARVIS] Sending to runtime...")
        
        try:
            response = requests.post(
                f"{self.server_url}/command",
                json={"command": command},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            print(f"[JARVIS] Server response: {result.get('message', 'Success')}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[JARVIS] Failed to send command: {e}")
            return False
