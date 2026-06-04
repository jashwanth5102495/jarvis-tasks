
"""
startup_manager.py
==================
Windows auto-startup registration manager for JARVIS.
Registers JARVIS to start automatically when user logs in.
"""

import logging
import sys
from pathlib import Path
import os
from typing import Optional

logger = logging.getLogger(__name__)


class StartupManager:
    def __init__(self):
        self._startup_folder: Optional[Path] = None

    def _get_startup_path(self) -> Path:
        if self._startup_folder:
            return self._startup_folder
        import getpass
        username = getpass.getuser()
        startup_dir = Path(
            f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        )
        self._startup_folder = startup_dir
        return startup_dir

    def enable_startup(self) -> bool:
        logger.info("Enabling JARVIS auto-startup")
        try:
            startup_path = self._get_startup_path()
            startup_path.mkdir(parents=True, exist_ok=True)
            jarvis_exe = Path(sys.executable).parent / "python.exe"
            jarvis_script = Path(__file__).parent.parent / "jarvis_runtime.py"
            batch_file = startup_path / "StartJARVIS.bat"
            with open(batch_file, "w", encoding="utf-8") as f:
                f.write(
                    f'@echo off\n'
                    f'cd "{jarvis_script.parent}"\n'
                    f'"{jarvis_exe}" "{jarvis_script}"\n'
                )
            logger.info(f"Auto-start enabled: {batch_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable auto-startup: {e}", exc_info=True)
            return False

    def disable_startup(self) -> bool:
        logger.info("Disabling JARVIS auto-startup")
        try:
            startup_path = self._get_startup_path()
            batch_file = startup_path / "StartJARVIS.bat"
            if batch_file.exists():
                batch_file.unlink()
                logger.info("Auto-start disabled")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to disable auto-startup: {e}", exc_info=True)
            return False


# Module-level singleton
startup_manager = StartupManager()

