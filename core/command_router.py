
import re
from jarvis_server.services.browser_service import open_youtube, open_chatgpt, search_google
from jarvis_server.services.app_launcher import launch_app
from jarvis_server.services.voice_service import say_hello


def route_command(command: str) -> tuple[bool, str]:
    command = command.lower().strip()

    if "youtube" in command:
        open_youtube()
        return (True, "Opened YouTube")
    elif "chatgpt" in command:
        open_chatgpt()
        return (True, "Opened ChatGPT")
    elif "google" in command:
        search_match = re.search(r'search google for (.+)', command, re.IGNORECASE)
        if search_match:
            query = search_match.group(1)
        else:
            query = command.replace("search", "").replace("google", "").strip()
        search_google(query)
        return (True, f"Searched Google for '{query}'")
    elif "brave" in command:
        result = launch_app("brave")
        if result:
            return (True, "Launched Brave")
        else:
            return (False, "Failed to launch Brave")
    elif "vscode" in command or "visual studio code" in command:
        result = launch_app("vscode")
        if result:
            return (True, "Launched VS Code")
        else:
            return (False, "Failed to launch VS Code")
    elif "spotify" in command:
        result = launch_app("spotify")
        if result:
            return (True, "Launched Spotify")
        else:
            return (False, "Failed to launch Spotify")
    elif "hello" in command or "say hello" in command:
        say_hello()
        return (True, "Said hello")
    else:
        return (False, f"Unknown command: {command}")
