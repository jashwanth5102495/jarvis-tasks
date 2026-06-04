"""
screenshot_manager.py
=====================
ScreenshotManager — capture, save, and manage screenshots.

Supported actions
-----------------
capture_screen    : full-screen screenshot → saved to workspace/screenshots/
capture_region    : region screenshot (x, y, width, height)
get_latest        : return path to the most recent screenshot
list_screenshots  : list all saved screenshots

Storage
-------
All screenshots saved to: workspace/screenshots/
Filename format: screenshot_YYYYMMDD_HHMMSS_<suffix>.png

Uses PyAutoGUI for capture + Pillow for saving.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from computer_control.failsafe import failsafe

logger = logging.getLogger(__name__)

_SCREENSHOT_DIR = Path(__file__).parent.parent / "workspace" / "screenshots"


class ScreenshotManager:
    """
    Captures and manages screenshots.

    Usage
    -----
    path = screenshot_manager.capture_screen()
    path = screenshot_manager.capture_region(100, 100, 800, 600)
    """

    SUPPORTED_ACTIONS = [
        "capture_screen", "capture_region", "get_latest", "list_screenshots",
    ]

    def __init__(self, screenshot_dir: Optional[Path] = None) -> None:
        self._dir = Path(screenshot_dir or _SCREENSHOT_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._latest: Optional[Path] = None

    # ── Public actions ─────────────────────────────────────────────────────────

    def capture_screen(self, suffix: str = "full") -> str:
        """Capture the full screen and save to disk."""
        failsafe.check()
        try:
            import pyautogui
            img = pyautogui.screenshot()
            path = self._save(img, suffix)
            self._latest = path
            logger.info(f"ScreenshotManager: full screen captured → {path}")
            return str(path)
        except Exception as exc:
            raise RuntimeError(f"Screenshot capture failed: {exc}") from exc

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        suffix: str = "region",
    ) -> str:
        """Capture a screen region and save to disk."""
        failsafe.check()
        try:
            import pyautogui
            img = pyautogui.screenshot(region=(x, y, width, height))
            path = self._save(img, suffix)
            self._latest = path
            logger.info(
                f"ScreenshotManager: region ({x},{y},{width},{height}) → {path}"
            )
            return str(path)
        except Exception as exc:
            raise RuntimeError(f"Region capture failed: {exc}") from exc

    def get_latest(self) -> str:
        if self._latest and self._latest.exists():
            return str(self._latest)
        # Fall back to most recent file in directory
        files = sorted(self._dir.glob("*.png"), key=lambda p: p.stat().st_mtime)
        if files:
            return str(files[-1])
        return "No screenshots found"

    def list_screenshots(self) -> str:
        files = sorted(self._dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return "No screenshots found"
        lines = [f"  {f.name}" for f in files[:20]]
        return f"Screenshots ({len(files)} total):\n" + "\n".join(lines)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _save(self, img, suffix: str) -> Path:
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"screenshot_{ts}_{suffix}.png"
        path = self._dir / name
        img.save(str(path))
        return path

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"ScreenshotManager: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)


# Module-level singleton
screenshot_manager = ScreenshotManager()
