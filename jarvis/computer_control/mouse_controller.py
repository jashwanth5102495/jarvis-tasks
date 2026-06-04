"""
mouse_controller.py
===================
MouseController — safe, logged mouse control via PyAutoGUI.

Supported actions
-----------------
move_to        : move mouse to (x, y) with smooth animation
click          : left-click at (x, y) or current position
double_click   : double left-click
right_click    : right-click
drag_to        : drag from current position to (x, y)
scroll         : scroll wheel up/down
get_position   : return current mouse position (SAFE)

All actions
  - check fail-safe before executing
  - clamp coordinates to screen bounds
  - log to action history
  - support configurable duration/delay
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple

from computer_control.cc_models import ActionRisk, ControllerType
from computer_control.failsafe import failsafe, FailSafeTriggered

logger = logging.getLogger(__name__)

# Default animation duration for smooth movement (seconds)
DEFAULT_MOVE_DURATION = 0.3
DEFAULT_CLICK_INTERVAL = 0.05


class MouseController:
    """
    Wraps PyAutoGUI mouse operations with fail-safe, bounds-checking,
    and structured logging.

    Usage
    -----
    mouse.move_to(500, 300)
    mouse.click(500, 300)
    mouse.scroll(clicks=3)
    """

    SUPPORTED_ACTIONS = [
        "move_to", "click", "double_click", "right_click",
        "drag_to", "scroll", "get_position",
    ]

    ACTION_RISK = {
        "move_to":      ActionRisk.MEDIUM,
        "click":        ActionRisk.HIGH,
        "double_click": ActionRisk.HIGH,
        "right_click":  ActionRisk.HIGH,
        "drag_to":      ActionRisk.HIGH,
        "scroll":       ActionRisk.MEDIUM,
        "get_position": ActionRisk.SAFE,
    }

    def __init__(self) -> None:
        self._import_pyautogui()

    def _import_pyautogui(self) -> None:
        try:
            import pyautogui
            self._pag = pyautogui
        except ImportError:
            raise ImportError(
                "pyautogui is required for MouseController. "
                "Install with: pip install pyautogui"
            )

    # ── Public actions ─────────────────────────────────────────────────────────

    def move_to(
        self,
        x: int,
        y: int,
        duration: float = DEFAULT_MOVE_DURATION,
    ) -> str:
        failsafe.check()
        x, y = failsafe.clamp_to_screen(x, y)
        self._pag.moveTo(x, y, duration=duration, tween=self._pag.easeInOutQuad)
        logger.info(f"MouseController: moved to ({x}, {y})")
        return f"Mouse moved to ({x}, {y})"

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1,
        interval: float = DEFAULT_CLICK_INTERVAL,
    ) -> str:
        failsafe.check()
        if x is not None and y is not None:
            x, y = failsafe.clamp_to_screen(x, y)
            self._pag.click(x, y, button=button, clicks=clicks, interval=interval)
            logger.info(f"MouseController: clicked ({x}, {y}) button={button}")
            return f"Clicked ({x}, {y}) [{button}]"
        else:
            self._pag.click(button=button, clicks=clicks, interval=interval)
            pos = self._pag.position()
            logger.info(f"MouseController: clicked at current position {pos}")
            return f"Clicked at current position {pos}"

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        failsafe.check()
        if x is not None and y is not None:
            x, y = failsafe.clamp_to_screen(x, y)
            self._pag.doubleClick(x, y)
            logger.info(f"MouseController: double-clicked ({x}, {y})")
            return f"Double-clicked ({x}, {y})"
        else:
            self._pag.doubleClick()
            return "Double-clicked at current position"

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        failsafe.check()
        if x is not None and y is not None:
            x, y = failsafe.clamp_to_screen(x, y)
            self._pag.rightClick(x, y)
            logger.info(f"MouseController: right-clicked ({x}, {y})")
            return f"Right-clicked ({x}, {y})"
        else:
            self._pag.rightClick()
            return "Right-clicked at current position"

    def drag_to(
        self,
        x: int,
        y: int,
        duration: float = DEFAULT_MOVE_DURATION,
        button: str = "left",
    ) -> str:
        failsafe.check()
        x, y = failsafe.clamp_to_screen(x, y)
        self._pag.dragTo(x, y, duration=duration, button=button)
        logger.info(f"MouseController: dragged to ({x}, {y})")
        return f"Dragged to ({x}, {y})"

    def scroll(self, clicks: int = 3, x: Optional[int] = None, y: Optional[int] = None) -> str:
        failsafe.check()
        if x is not None and y is not None:
            x, y = failsafe.clamp_to_screen(x, y)
            self._pag.scroll(clicks, x=x, y=y)
        else:
            self._pag.scroll(clicks)
        direction = "up" if clicks > 0 else "down"
        logger.info(f"MouseController: scrolled {abs(clicks)} clicks {direction}")
        return f"Scrolled {abs(clicks)} clicks {direction}"

    def get_position(self) -> str:
        pos = self._pag.position()
        return f"Mouse position: ({pos.x}, {pos.y})"

    def screen_size(self) -> Tuple[int, int]:
        return self._pag.size()

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        """Dispatch by action name string."""
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"MouseController: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)
