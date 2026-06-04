"""
window_manager.py
=================
WindowManager — list, focus, resize, and query desktop windows.

Uses pygetwindow (bundled with PyAutoGUI on Windows).

Supported actions
-----------------
list_windows      : return all visible window titles
focus_window      : bring a window to the foreground by title substring
maximize_window   : maximize a window
minimize_window   : minimize a window
get_active_window : return the title of the currently active window
close_window      : close a window (HIGH risk — requires approval)
window_exists     : check if a window with a given title exists (SAFE)

Safety
------
- close_window is HIGH risk and requires explicit user approval
- Window targeting uses substring matching (case-insensitive)
- If multiple windows match, the first match is used
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from computer_control.cc_models import ActionRisk
from computer_control.failsafe import failsafe

logger = logging.getLogger(__name__)


class WindowManager:
    """
    Manages desktop windows via pygetwindow.

    Usage
    -----
    window_manager.focus_window("Chrome")
    window_manager.maximize_window("VS Code")
    titles = window_manager.list_windows()
    """

    SUPPORTED_ACTIONS = [
        "list_windows", "focus_window", "maximize_window",
        "minimize_window", "get_active_window", "close_window",
        "window_exists",
    ]

    ACTION_RISK = {
        "list_windows":      ActionRisk.SAFE,
        "focus_window":      ActionRisk.MEDIUM,
        "maximize_window":   ActionRisk.MEDIUM,
        "minimize_window":   ActionRisk.MEDIUM,
        "get_active_window": ActionRisk.SAFE,
        "close_window":      ActionRisk.HIGH,
        "window_exists":     ActionRisk.SAFE,
    }

    def __init__(self) -> None:
        try:
            import pygetwindow as gw
            self._gw = gw
        except ImportError:
            raise ImportError(
                "pygetwindow is required for WindowManager. "
                "It is bundled with pyautogui: pip install pyautogui"
            )

    # ── Public actions ─────────────────────────────────────────────────────────

    def list_windows(self) -> str:
        failsafe.check()
        titles = [t for t in self._gw.getAllTitles() if t.strip()]
        if not titles:
            return "No windows found"
        lines = "\n".join(f"  • {t}" for t in sorted(set(titles))[:30])
        logger.info(f"WindowManager: listed {len(titles)} windows")
        return f"Open windows ({len(titles)}):\n{lines}"

    def focus_window(self, title: str) -> str:
        failsafe.check()
        win = self._find_window(title)
        if win is None:
            raise ValueError(f"No window found matching {title!r}")
        try:
            win.activate()
            time.sleep(0.3)   # allow OS to bring window to front
            logger.info(f"WindowManager: focused {win.title!r}")
            return f"Focused window: {win.title!r}"
        except Exception as exc:
            # Some windows raise on activate() — try restore first
            try:
                win.restore()
                win.activate()
                return f"Focused window: {win.title!r}"
            except Exception:
                raise RuntimeError(f"Could not focus window {title!r}: {exc}") from exc

    def maximize_window(self, title: str) -> str:
        failsafe.check()
        win = self._find_window(title)
        if win is None:
            raise ValueError(f"No window found matching {title!r}")
        win.maximize()
        logger.info(f"WindowManager: maximized {win.title!r}")
        return f"Maximized: {win.title!r}"

    def minimize_window(self, title: str) -> str:
        failsafe.check()
        win = self._find_window(title)
        if win is None:
            raise ValueError(f"No window found matching {title!r}")
        win.minimize()
        logger.info(f"WindowManager: minimized {win.title!r}")
        return f"Minimized: {win.title!r}"

    def get_active_window(self) -> str:
        failsafe.check()
        try:
            win = self._gw.getActiveWindow()
            title = win.title if win else "No active window"
            logger.info(f"WindowManager: active window = {title!r}")
            return f"Active window: {title!r}"
        except Exception as exc:
            return f"Could not get active window: {exc}"

    def close_window(self, title: str) -> str:
        """Close a window — HIGH risk, requires user approval."""
        failsafe.check()
        win = self._find_window(title)
        if win is None:
            raise ValueError(f"No window found matching {title!r}")
        win.close()
        logger.info(f"WindowManager: closed {win.title!r}")
        return f"Closed: {win.title!r}"

    def window_exists(self, title: str) -> str:
        win = self._find_window(title)
        exists = win is not None
        return f"Window {title!r} exists: {exists}"

    # ── Internal ───────────────────────────────────────────────────────────────

    def _find_window(self, title: str):
        """Find first window whose title contains `title` (case-insensitive)."""
        title_lower = title.lower()
        for win in self._gw.getAllWindows():
            if win.title and title_lower in win.title.lower():
                return win
        return None

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"WindowManager: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)
