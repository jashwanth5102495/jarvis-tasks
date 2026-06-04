
import time
import requests
import webbrowser
import subprocess
import os
import pyttsx3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[JARVIS] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
VERCEL_API_URL = "https://jar-git-main-blunets-projects.vercel.app"
API_TOKEN = os.getenv("JARVIS_API_TOKEN", "test-token")  # Set this environment variable!
POLL_INTERVAL = 2  # seconds

# Initialize TTS engine
try:
    tts_engine = pyttsx3.init()
    voices = tts_engine.getProperty('voices')
    tts_engine.setProperty('voice', voices[0].id)
except Exception as e:
    logger.warning(f"TTS initialization failed: {e}")
    tts_engine = None


def speak(text):
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS failed: {e}")
    else:
        logger.info(f"[TTS] {text}")


def execute_command(command_text):
    """Execute local command based on text."""
    command = command_text.lower().strip()
    logger.info(f"Executing command: {command}")
    
    try:
        if "youtube" in command:
            webbrowser.open("https://youtube.com")
            return True
        elif "brave" in command:
            # Common Windows paths for Brave
            brave_paths = [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
            ]
            for path in brave_paths:
                if os.path.exists(path):
                    subprocess.Popen(path)
                    return True
            logger.warning("Brave not found, opening default browser")
            webbrowser.open("https://brave.com")
            return True
        elif "vscode" in command or "visual studio code" in command:
            # Try code command
            try:
                subprocess.Popen("code")
                return True
            except Exception:
                # Common Windows paths for VS Code
                vscode_paths = [
                    r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getlogin()),
                    r"C:\Program Files\Microsoft VS Code\Code.exe",
                    r"C:\Program Files (x86)\Microsoft VS Code\Code.exe"
                ]
                for path in vscode_paths:
                    if os.path.exists(path):
                        subprocess.Popen(path)
                        return True
                logger.error("VS Code not found")
                return False
        elif "spotify" in command:
            # Try spotify command
            try:
                subprocess.Popen("spotify")
                return True
            except Exception:
                webbrowser.open("https://open.spotify.com")
                return True
        elif "say hello" in command or "hello" in command:
            speak("Hello! How can I assist you today?")
            return True
        else:
            logger.warning(f"Unsupported command: {command}")
            return False
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return False


def get_latest_command():
    """Fetch latest pending command from Vercel API."""
    try:
        response = requests.get(
            f"{VERCEL_API_URL}/api/latest-command",
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data and not data.get("command") is None and data.get("status") == "pending":
                return data
        return None
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch command: {e}")
        return None


def update_command_status(command_id, status):
    """Update command status on Vercel API."""
    try:
        response = requests.post(
            f"{VERCEL_API_URL}/api/command-status",
            headers={"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"},
            json={"id": command_id, "status": status},
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"Command {command_id} status updated to {status}")
            return True
        else:
            logger.warning(f"Failed to update status: {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.warning(f"Failed to update status: {e}")
        return False


def main():
    logger.info("Poller started...")
    logger.info("Waiting for commands...")
    
    try:
        while True:
            command_data = get_latest_command()
            
            if command_data:
                command_id = command_data["id"]
                command_text = command_data["command"]
                logger.info(f"Received command: {command_text}")
                
                logger.info("Executing...")
                success = execute_command(command_text)
                
                if success:
                    logger.info("Command completed")
                    update_command_status(command_id, "completed")
                else:
                    logger.error("Command failed")
                    update_command_status(command_id, "failed")
            
            time.sleep(POLL_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("Poller stopped by user")
    except Exception as e:
        logger.error(f"Poller crashed: {e}")
        logger.info("Restarting in 5 seconds...")
        time.sleep(5)
        main()


if __name__ == "__main__":
    main()
