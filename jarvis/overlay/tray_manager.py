
"""
tray_manager.py
===============
Enhanced system tray integration for JARVIS using pystray and PIL.
Provides pause/resume, voice mode, and exit options.
"""

import logging
import threading
from typing import Optional
from pathlib import Path

from jarvis.runtime.runtime_state import RuntimeStatus

logger = logging.getLogger(__name__)


class TrayManager:
    def __init__(self):
        self._tray_icon: Optional[object] = None
        self._tray_thread: Optional[threading.Thread] = None
        self._pystray: Optional[object] = None
        self._Image: Optional[object] = None
        self._voice_enabled: bool = True
        logger.info("Tray Manager (UI) initialized")

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
        img = Image.new('RGB', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if status == RuntimeStatus.PAUSED:
            fill_color = (150, 150, 150)
        elif status == RuntimeStatus.LISTENING:
            fill_color = (0, 136, 255)
        elif status == RuntimeStatus.SPEAKING:
            fill_color = (0, 204, 255)
        elif status == RuntimeStatus.EXECUTING:
            fill_color = (136, 204, 0)
        else:
            fill_color = (0, 170, 255)
        draw.ellipse([(10, 10), (54, 54)], fill=fill_color)
        return img

    def _on_pause_click(self, icon, item) -> None:
        from jarvis.runtime.runtime_manager import runtime_manager
        logger.info("Tray: Pause/Resume clicked")
        runtime_manager.toggle_pause()

    def _on_voice_toggle(self, icon, item) -> None:
        logger.info("Tray: Voice mode toggled")
        self._voice_enabled = not self._voice_enabled
        # TODO: Integrate with actual voice system
        logger.info(f"Voice mode: {'enabled' if self._voice_enabled else 'disabled'}")

    def _on_open_dashboard(self, icon, item) -> None:
        logger.info("Tray: Open Dashboard clicked")
        # TODO: Implement dashboard

    def _on_exit_click(self, icon, item) -> None:
        from jarvis.runtime.runtime_manager import runtime_manager
        logger.info("Tray: Exit clicked")
        icon.stop()
        runtime_manager.shutdown()

    def start(self) -> None:
        if not self._pystray:
            return
        if self._tray_thread and self._tray_thread.is_alive():
            return

        from jarvis.runtime.runtime_state import runtime_state
        menu_items = [
            self._pystray.MenuItem("Pause/Resume", self._on_pause_click, default=True),
            self._pystray.Menu.SEPARATOR,
            self._pystray.MenuItem("Enable Voice Mode", self._on_voice_toggle, checked=lambda item: self._voice_enabled),
            self._pystray.Menu.SEPARATOR,
            self._pystray.MenuItem("Open Dashboard", self._on_open_dashboard),
            self._pystray.Menu.SEPARATOR,
            self._pystray.MenuItem("Exit JARVIS", self._on_exit_click)
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


tray_manager = TrayManager()

