
import os
import sys
import winreg
from pathlib import Path


def get_startup_folder_path() -> Path:
    app_data = os.environ.get("APPDATA")
    if not app_data:
        raise RuntimeError("Could not find APPDATA environment variable")
    return Path(app_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def create_shortcut(target_path: Path, shortcut_name: str = "Jarvis Runtime.lnk") -> None:
    import win32com.client

    startup_folder = get_startup_folder_path()
    shortcut_path = startup_folder / shortcut_name

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = str(target_path)
    shortcut.WorkingDirectory = str(target_path.parent)
    shortcut.save()

    print(f"[Startup Manager] Shortcut created at: {shortcut_path}")


def remove_shortcut(shortcut_name: str = "Jarvis Runtime.lnk") -> None:
    startup_folder = get_startup_folder_path()
    shortcut_path = startup_folder / shortcut_name
    if shortcut_path.exists():
        shortcut_path.unlink()
        print(f"[Startup Manager] Shortcut removed: {shortcut_path}")
    else:
        print("[Startup Manager] Shortcut not found")


def is_startup_enabled(shortcut_name: str = "Jarvis Runtime.lnk") -> bool:
    startup_folder = get_startup_folder_path()
    shortcut_path = startup_folder / shortcut_name
    return shortcut_path.exists()
