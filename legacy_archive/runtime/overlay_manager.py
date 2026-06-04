
"""
overlay_manager.py
==================
Tkinter-based lightweight status overlay for JARVIS.
Shows "Personal A.I is Active/Paused" in a small, transparent corner widget.
"""

import logging
import threading
from typing import Optional

from runtime.runtime_state import RuntimeStatus

logger = logging.getLogger(__name__)


class OverlayManager:
    def __init__(self):
        self._root: Optional[object] = None
        self._label: Optional[object] = None
        self._overlay_thread: Optional[threading.Thread] = None
        self._tkinter: Optional[object] = None

    def initialize(self) -> None:
        logger.info("Initializing overlay manager")
        try:
            import tkinter as tk
            self._tkinter = tk
            logger.debug("Tkinter imported successfully")
        except ImportError:
            logger.warning("Tkinter not found; overlay disabled")
            self._tkinter = None

    def _create_overlay(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._root = tk.Tk()
        self._root.title("JARVIS Status Overlay")
        self._root.attributes('-topmost', True)
        self._root.attributes('-transparentcolor', '#000000')
        self._root.configure(bg='#000000')
        self._root.overrideredirect(True)  # No window borders
        self._root.geometry('+10+10')  # Position top-left (10,10)

        style = ttk.Style()
        style.configure(
            'Overlay.TLabel',
            font=('Arial', 14, 'bold'),
            foreground='#00ff88',
            background='#000000',
            padding=5
        )
        self._label = ttk.Label(
            self._root,
            text='Personal A.I is Active',
            style='Overlay.TLabel'
        )
        self._label.pack()

    def start(self) -> None:
        if not self._tkinter:
            return
        if self._overlay_thread and self._overlay_thread.is_alive():
            return
        self._overlay_thread = threading.Thread(
            target=self._run_overlay,
            daemon=True,
            name="OverlayUI"
        )
        self._overlay_thread.start()
        logger.info("Overlay manager started")

    def _run_overlay(self) -> None:
        if self._tkinter:
            self._create_overlay()
            if self._root:
                self._root.mainloop()

    def update_status_display(self, status: RuntimeStatus) -> None:
        if not self._tkinter or not self._label:
            return

        def _update_text():
            if self._label and self._root:
                if status == RuntimeStatus.PAUSED:
                    self._label.config(text='Personal A.I is Paused', foreground='#ffaa00')
                elif status == RuntimeStatus.LISTENING:
                    self._label.config(text='Personal A.I is Listening', foreground='#00aaff')
                elif status == RuntimeStatus.SPEAKING:
                    self._label.config(text='Personal A.I is Speaking', foreground='#ff00aa')
                elif status == RuntimeStatus.EXECUTING:
                    self._label.config(text='Personal A.I is Executing', foreground='#aaff00')
                else:
                    self._label.config(text='Personal A.I is Active', foreground='#00ff88')
        try:
            self._root.after(0, _update_text)
        except Exception as e:
            logger.warning(f"Overlay update failed: {e}")

    def stop(self) -> None:
        logger.info("Stopping overlay manager")
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except Exception as e:
                logger.warning(f"Error stopping overlay: {e}")


# Module-level singleton
overlay_manager = OverlayManager()

