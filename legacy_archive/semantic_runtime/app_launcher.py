
"""
app_launcher.py
===============
Dynamic app launcher and discovery system for JARVIS AI OS.
Discovers installed Windows apps from Start Menu and Program Files.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from computer_control.app_registry import app_registry, AppEntry

logger = logging.getLogger(__name__)


class AppLauncher:
    def __init__(self):
        logger.info("App Launcher initialized")

    def discover_windows_apps(self) -> List[AppEntry]:
        """Discover installed apps from common Windows locations."""
        apps = []
        start_menu_paths = [
            Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get("ProgramData", "C:/ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ]
        for start_menu in start_menu_paths:
            if start_menu.exists():
                for shortcut in start_menu.rglob("*.lnk"):
                    apps.append(self._parse_shortcut(shortcut))
        return apps

    def _parse_shortcut(self, shortcut_path: Path) -> Optional[AppEntry]:
        try:
            # Try using pywin32 to parse shortcuts
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            target = shortcut.TargetPath
            if target:
                name = shortcut_path.stem
                return AppEntry(
                    canonical=name.lower().replace(" ", "_"),
                    executable=target,
                    aliases=[name.lower(), shortcut_path.stem.lower()],
                    description=name
                )
        except ImportError:
            logger.warning("pywin32 not installed, can't parse .lnk shortcuts")
        except Exception as e:
            logger.warning(f"Failed to parse shortcut {shortcut_path}: {e}")
        return None

    def launch(self, app_name: str) -> str:
        logger.info(f"Launching app: {app_name}")
        return app_registry.resolve(app_name)


app_launcher = AppLauncher()
