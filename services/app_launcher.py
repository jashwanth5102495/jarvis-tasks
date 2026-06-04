
import subprocess
import os
import sys


def get_windows_app_paths(app_name: str) -> list[str]:
    paths = []
    username = os.getlogin()
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    app_data_local = os.environ.get("LOCALAPPDATA", f"C:\\Users\\{username}\\AppData\\Local")

    if app_name == "brave":
        paths.append(os.path.join(program_files, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"))
        paths.append(os.path.join(program_files_x86, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"))
        paths.append(os.path.join(app_data_local, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"))
    elif app_name == "vscode":
        paths.append("code")
        paths.append(os.path.join(app_data_local, "Programs", "Microsoft VS Code", "Code.exe"))
        paths.append(os.path.join(program_files, "Microsoft VS Code", "Code.exe"))
        paths.append(os.path.join(program_files_x86, "Microsoft VS Code", "Code.exe"))
    elif app_name == "spotify":
        paths.append("spotify")
        paths.append(os.path.join(app_data_local, "Spotify", "Spotify.exe"))
    return paths


def launch_app(app_name: str) -> bool:
    print(f"[JARVIS] Attempting to launch {app_name}")
    paths = get_windows_app_paths(app_name)
    for path in paths:
        if path in ["code", "spotify"]:
            try:
                subprocess.Popen([path], shell=True)
                print(f"[JARVIS] Launched {app_name} successfully")
                return True
            except Exception as e:
                print(f"[JARVIS] Failed to launch {path}: {e}")
                continue
        print(f"[JARVIS] Checking path: {path}")
        if os.path.exists(path):
            print(f"[JARVIS] {app_name} path found: {path}")
            try:
                subprocess.Popen([path])
                print(f"[JARVIS] Launched {app_name} successfully")
                return True
            except Exception as e:
                print(f"[JARVIS] Failed to launch {path}: {e}")
                continue
    print(f"[JARVIS] {app_name} browser not installed.")
    return False
