
"""
tray_manager.py
===============
System tray integration for JARVIS using pystray and PIL for icons.
"""

import logging
import threading
from typing import Optional
from pathlib import Path

from runtime.runtime_state import RuntimeStatus

logger = logging.getLogger(__name__)


class TrayManager:
    def __init__(self):
        self._tray_icon: Optional[object] = None
        self._tray_thread: Optional[threading.Thread] = None
        self._pystray: Optional[object] = None
        self._Image: Optional[object] = None

    def initialize(self) -> None:
        logger.info("Initializing tray manager")
        try:
            import pystray
            from PIL import Image, ImageDraw
            self._pystray = pystray
            self._Image = Image
            self._ImageDraw = ImageDraw
            logger.debug("Tray libraries imported successfully")
        except ImportError:
            logger.warning("pystray/PIL not found; tray icon disabled")
            self._pystray = None

    def _create_icon(self, status: RuntimeStatus) -> object:
        from PIL import Image, ImageDraw
        # Create a simple circular icon as placeholder (green=active, yellow=paused)
        img = Image.new('RGB', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Pick color based on status
        if status == RuntimeStatus.PAUSED:
            fill_color = (255, 200, 0)  # Yellow/orange
        elif status == RuntimeStatus.LISTENING:
            fill_color = (0, 100, 255)  # Blue
        elif status == RuntimeStatus.SPEAKING:
            fill_color = (255, 0, 100)  # Pink/red
        else:
            fill_color = (0, 255, 100)  # Green
        draw.ellipse([(10, 10), (54, 54)], fill=fill_color)
        return img

    def _on_pause_click(self, icon, item) -> None:
        from runtime.runtime_manager import runtime_manager
        logger.info("Tray: Pause/Resume clicked")
        runtime_manager.toggle_pause()

    def _on_exit_click(self, icon, item) -> None:
        from runtime.runtime_manager import runtime_manager
        logger.info("Tray: Exit clicked")
        icon.stop()
        runtime_manager.shutdown()

    def start(self) -> None:
        if not self._pystray:
            return
        if self._tray_thread and self._tray_thread.is_alive():
            return

        from runtime.runtime_state import runtime_state
        menu_items = [
            self._pystray.MenuItem(
                "Pause/Resume",
                self._on_pause_click,
                default=True
            ),
            self._pystray.Menu.SEPARATOR,
            self._pystray.MenuItem(
                "Exit JARVIS",
                self._on_exit_click
            )
        ]
        icon_image = self._create_icon(runtime_state.current_status)
        self._tray_icon = self._pystray.Icon(
            "JARVIS",
            icon_image,
            "JARVIS AI Assistant",
            menu_items
        )
        self._tray_thread = threading.Thread(
            target=self._run_tray,
            daemon=True,
            name="TrayIcon"
        )
        self._tray_thread.start()
        logger.info("Tray manager started")

    def _run_tray(self) -> None:
        if self._tray_icon:
            self._tray_icon.run()

    def update_tray_icon(self, status: RuntimeStatus) -> None:
        if not self._pystray or not self._tray_icon:
            return
        new_img = self._create_icon(status)
        self._tray_icon.icon = new_img
        self._tray_icon.title = "JARVIS - " + status.name.replace("_", " ").title()

    def stop(self) -> None:
        logger.info("Stopping tray manager")
        if self._tray_icon:
            self._tray_icon.stop()


# Module-level singleton
tray_manager = TrayManager()

