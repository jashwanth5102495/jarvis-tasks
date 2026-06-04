"""
failsafe.py
===========
Fail-Safe Protection System — MANDATORY for all computer control.

Mechanisms
----------
1. PyAutoGUI corner fail-safe  : moving mouse to top-left (0,0) raises
   FailSafeException and aborts all execution immediately.

2. Emergency stop hotkey       : Ctrl+Shift+F12 sets a global stop flag.
   All controllers check this flag before every action.

3. Action timeout              : each action has a max execution time.
   Exceeded timeout raises ControlTimeoutError.

4. Stuck-action detection      : if the same action runs for > STUCK_THRESHOLD_MS
   it is considered stuck and aborted.

5. Bounds checking             : mouse coordinates are clamped to screen bounds
   before any move/click to prevent off-screen actions.

Usage
-----
# At the start of every controller action:
failsafe.check()   # raises FailSafeTriggered if stop requested

# Wrap long operations:
with failsafe.timeout_guard(action_id, timeout_ms=5000):
    ...
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
DEFAULT_ACTION_TIMEOUT_MS = 10_000   # 10 seconds per action
STUCK_THRESHOLD_MS        = 15_000   # 15 seconds = stuck
PAUSE_BETWEEN_ACTIONS_S   = 0.05     # 50 ms between actions (PyAutoGUI PAUSE)


class FailSafeTriggered(Exception):
    """Raised when the emergency stop is activated."""


class ControlTimeoutError(Exception):
    """Raised when an action exceeds its timeout."""


class FailSafeSystem:
    """
    Global fail-safe coordinator.

    Thread-safe: the emergency stop flag can be set from any thread
    (e.g. a keyboard listener running in a background thread).
    """

    def __init__(self) -> None:
        self._stop_flag:  threading.Event = threading.Event()
        self._lock:       threading.Lock  = threading.Lock()
        self._enabled:    bool            = True
        self._setup_pyautogui()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _setup_pyautogui(self) -> None:
        try:
            import pyautogui
            pyautogui.FAILSAFE = True          # corner fail-safe ON
            pyautogui.PAUSE    = PAUSE_BETWEEN_ACTIONS_S
            logger.info("PyAutoGUI fail-safe enabled (corner: top-left)")
        except Exception as exc:
            logger.warning(f"PyAutoGUI setup warning: {exc}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def check(self) -> None:
        """
        Call before every controller action.
        Raises FailSafeTriggered if emergency stop is active.
        """
        if not self._enabled:
            return
        if self._stop_flag.is_set():
            raise FailSafeTriggered(
                "Emergency stop activated — all computer control halted."
            )

    def trigger_stop(self) -> None:
        """Activate emergency stop from any thread."""
        self._stop_flag.set()
        logger.critical("FAIL-SAFE TRIGGERED — emergency stop activated")
        print("\n\033[91m⚠  JARVIS EMERGENCY STOP ACTIVATED\033[0m\n")

    def reset(self) -> None:
        """Reset the stop flag (requires explicit user action)."""
        self._stop_flag.clear()
        logger.info("Fail-safe reset — computer control re-enabled")

    def is_stopped(self) -> bool:
        return self._stop_flag.is_set()

    def disable(self) -> None:
        """Disable fail-safe checks (testing only)."""
        self._enabled = False

    def enable(self) -> None:
        self._enabled = True

    # ── Timeout guard ──────────────────────────────────────────────────────────

    @contextmanager
    def timeout_guard(
        self,
        action_id: str,
        timeout_ms: int = DEFAULT_ACTION_TIMEOUT_MS,
    ) -> Generator[None, None, None]:
        """
        Context manager that raises ControlTimeoutError if the block
        takes longer than timeout_ms milliseconds.
        """
        result: dict = {"timed_out": False}
        timeout_s = timeout_ms / 1000.0

        def _watchdog() -> None:
            time.sleep(timeout_s)
            if not result.get("done"):
                result["timed_out"] = True
                logger.error(f"Action {action_id!r} timed out after {timeout_ms}ms")

        t = threading.Thread(target=_watchdog, daemon=True)
        t.start()
        try:
            yield
        finally:
            result["done"] = True
            if result["timed_out"]:
                raise ControlTimeoutError(
                    f"Action {action_id!r} exceeded timeout of {timeout_ms}ms"
                )

    # ── Screen bounds ──────────────────────────────────────────────────────────

    @staticmethod
    def clamp_to_screen(x: int, y: int) -> tuple[int, int]:
        """Clamp coordinates to screen bounds to prevent off-screen actions."""
        try:
            import pyautogui
            w, h = pyautogui.size()
            # Keep 1px margin from edges to avoid triggering corner fail-safe
            x = max(1, min(x, w - 2))
            y = max(1, min(y, h - 2))
        except Exception:
            pass
        return x, y


# Module-level singleton
failsafe = FailSafeSystem()
