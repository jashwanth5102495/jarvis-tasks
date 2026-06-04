"""
ui_locator.py
=============
UILocator — find UI elements on screen using image matching.

Uses PyAutoGUI's locateOnScreen() (backed by OpenCV) to find
template images on the current screen.

Supported actions
-----------------
locate_image      : find a template image on screen → ScreenRegion
locate_and_click  : find image and click its center
wait_for_image    : wait until an image appears on screen
image_exists      : check if an image is currently visible (SAFE)

Template images
---------------
Store reference images in: workspace/ui_templates/
Pass relative paths like "chrome_icon.png" — the locator
resolves them against the templates directory.

Confidence threshold
--------------------
Default: 0.8 (80% match confidence)
Lower for fuzzy matching, raise for precision.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from computer_control.cc_models import ActionRisk, ScreenRegion
from computer_control.failsafe import failsafe

logger = logging.getLogger(__name__)

_TEMPLATES_DIR    = Path(__file__).parent.parent / "workspace" / "ui_templates"
DEFAULT_CONFIDENCE = 0.8
DEFAULT_TIMEOUT_S  = 10
RETRY_INTERVAL_S   = 0.5


class UILocator:
    """
    Locates UI elements on screen using template image matching.

    Usage
    -----
    region = ui_locator.locate_image("submit_button.png")
    ui_locator.locate_and_click("ok_button.png")
    """

    SUPPORTED_ACTIONS = [
        "locate_image", "locate_and_click", "wait_for_image", "image_exists",
    ]

    ACTION_RISK = {
        "locate_image":     ActionRisk.SAFE,
        "locate_and_click": ActionRisk.HIGH,
        "wait_for_image":   ActionRisk.SAFE,
        "image_exists":     ActionRisk.SAFE,
    }

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        self._templates_dir = Path(templates_dir or _TEMPLATES_DIR)
        self._templates_dir.mkdir(parents=True, exist_ok=True)

    # ── Public actions ─────────────────────────────────────────────────────────

    def locate_image(
        self,
        image_path: str,
        confidence: float = DEFAULT_CONFIDENCE,
    ) -> str:
        failsafe.check()
        full_path = self._resolve(image_path)
        try:
            import pyautogui
            location = pyautogui.locateOnScreen(
                str(full_path), confidence=confidence
            )
            if location is None:
                return f"Image not found: {image_path!r}"
            region = ScreenRegion(
                x=location.left, y=location.top,
                width=location.width, height=location.height,
                label=image_path,
            )
            logger.info(f"UILocator: found {image_path!r} at {region.center}")
            return (
                f"Found {image_path!r} at center={region.center}, "
                f"region={region.as_tuple}"
            )
        except Exception as exc:
            return f"Locate failed for {image_path!r}: {exc}"

    def locate_and_click(
        self,
        image_path: str,
        confidence: float = DEFAULT_CONFIDENCE,
    ) -> str:
        failsafe.check()
        full_path = self._resolve(image_path)
        try:
            import pyautogui
            location = pyautogui.locateOnScreen(
                str(full_path), confidence=confidence
            )
            if location is None:
                raise ValueError(f"Image not found on screen: {image_path!r}")
            center = pyautogui.center(location)
            pyautogui.click(center)
            logger.info(f"UILocator: clicked {image_path!r} at {center}")
            return f"Clicked {image_path!r} at {center}"
        except Exception as exc:
            raise RuntimeError(f"locate_and_click failed: {exc}") from exc

    def wait_for_image(
        self,
        image_path: str,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        confidence: float = DEFAULT_CONFIDENCE,
    ) -> str:
        failsafe.check()
        full_path = self._resolve(image_path)
        start = time.time()
        while time.time() - start < timeout_s:
            failsafe.check()
            try:
                import pyautogui
                location = pyautogui.locateOnScreen(
                    str(full_path), confidence=confidence
                )
                if location is not None:
                    logger.info(f"UILocator: {image_path!r} appeared after "
                                f"{time.time()-start:.1f}s")
                    return f"Image appeared: {image_path!r}"
            except Exception:
                pass
            time.sleep(RETRY_INTERVAL_S)
        return f"Timeout: {image_path!r} did not appear within {timeout_s}s"

    def image_exists(
        self,
        image_path: str,
        confidence: float = DEFAULT_CONFIDENCE,
    ) -> str:
        full_path = self._resolve(image_path)
        try:
            import pyautogui
            location = pyautogui.locateOnScreen(
                str(full_path), confidence=confidence
            )
            exists = location is not None
            return f"Image {image_path!r} visible: {exists}"
        except Exception as exc:
            return f"Image check failed: {exc}"

    # ── Internal ───────────────────────────────────────────────────────────────

    def _resolve(self, image_path: str) -> Path:
        p = Path(image_path)
        if p.is_absolute():
            return p
        return self._templates_dir / image_path

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"UILocator: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)


# Module-level singleton
ui_locator = UILocator()
