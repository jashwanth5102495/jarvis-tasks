"""
keyboard_controller.py
======================
KeyboardController — safe, logged keyboard control via PyAutoGUI.

Supported actions
-----------------
type_text      : type a string with configurable interval
press          : press a single key (enter, tab, escape, …)
hotkey         : press a key combination (ctrl+s, ctrl+c, …)
key_down       : hold a key down
key_up         : release a held key
clear_field    : select-all + delete (clears a text field)

Safety
------
- All actions check fail-safe before executing
- Typing interval prevents overwhelming the target application
- Maximum text length enforced to prevent runaway typing
- Dangerous key combinations (Alt+F4, Win+R, etc.) are blocked
"""

from __future__ import annotations

import logging
import time
from typing import List

from computer_control.cc_models import ActionRisk
from computer_control.failsafe import failsafe

logger = logging.getLogger(__name__)

# Safety limits
DEFAULT_TYPE_INTERVAL = 0.04    # seconds between keystrokes
MAX_TEXT_LENGTH       = 2000    # characters
DEFAULT_KEY_PAUSE     = 0.1     # seconds after each key press

# Blocked hotkey combinations (destructive or system-level)
_BLOCKED_HOTKEYS: List[tuple] = [
    ("alt", "f4"),
    ("win", "r"),
    ("win", "x"),
    ("ctrl", "alt", "del"),
    ("ctrl", "alt", "t"),
    ("win", "d"),
    ("alt", "tab"),   # window switching — too disruptive
]


class KeyboardController:
    """
    Wraps PyAutoGUI keyboard operations with fail-safe and safety checks.

    Usage
    -----
    keyboard.type_text("Hello JARVIS")
    keyboard.press("enter")
    keyboard.hotkey("ctrl", "s")
    """

    SUPPORTED_ACTIONS = [
        "type_text", "press", "hotkey", "key_down", "key_up", "clear_field",
    ]

    ACTION_RISK = {
        "type_text":   ActionRisk.HIGH,
        "press":       ActionRisk.HIGH,
        "hotkey":      ActionRisk.HIGH,
        "key_down":    ActionRisk.HIGH,
        "key_up":      ActionRisk.HIGH,
        "clear_field": ActionRisk.HIGH,
    }

    def __init__(self) -> None:
        try:
            import pyautogui
            self._pag = pyautogui
        except ImportError:
            raise ImportError("pyautogui is required for KeyboardController.")

    # ── Public actions ─────────────────────────────────────────────────────────

    def type_text(
        self,
        text: str,
        interval: float = DEFAULT_TYPE_INTERVAL,
    ) -> str:
        failsafe.check()
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(
                f"Text too long ({len(text)} chars). "
                f"Maximum is {MAX_TEXT_LENGTH} characters."
            )
        self._pag.typewrite(text, interval=interval)
        preview = text[:40] + ("…" if len(text) > 40 else "")
        logger.info(f"KeyboardController: typed {len(text)} chars: {preview!r}")
        return f"Typed: {preview!r}"

    def press(self, key: str, presses: int = 1, interval: float = DEFAULT_KEY_PAUSE) -> str:
        failsafe.check()
        self._pag.press(key, presses=presses, interval=interval)
        logger.info(f"KeyboardController: pressed {key!r} × {presses}")
        return f"Pressed: {key!r} × {presses}"

    def hotkey(self, *keys: str, **kwargs) -> str:
        failsafe.check()
        # Support both hotkey("ctrl","s") and hotkey(keys=["ctrl","s"])
        if not keys and "keys" in kwargs:
            keys = tuple(kwargs["keys"])
        keys_lower = tuple(k.lower() for k in keys)
        if keys_lower in _BLOCKED_HOTKEYS:
            raise ValueError(
                f"Hotkey {keys} is blocked for safety. "
                f"Blocked combinations: {_BLOCKED_HOTKEYS}"
            )
        self._pag.hotkey(*keys)
        combo = "+".join(keys)
        logger.info(f"KeyboardController: hotkey {combo!r}")
        return f"Hotkey: {combo}"

    def key_down(self, key: str) -> str:
        failsafe.check()
        self._pag.keyDown(key)
        logger.info(f"KeyboardController: key_down {key!r}")
        return f"Key down: {key!r}"

    def key_up(self, key: str) -> str:
        failsafe.check()
        self._pag.keyUp(key)
        logger.info(f"KeyboardController: key_up {key!r}")
        return f"Key up: {key!r}"

    def clear_field(self) -> str:
        """Select all text in the focused field and delete it."""
        failsafe.check()
        self._pag.hotkey("ctrl", "a")
        time.sleep(0.05)
        self._pag.press("delete")
        logger.info("KeyboardController: cleared field")
        return "Field cleared"

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"KeyboardController: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)
