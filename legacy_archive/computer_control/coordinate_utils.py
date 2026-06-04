"""
coordinate_utils.py
===================
Screen coordinate helpers used by the ActionTranslator and controllers.

All functions are pure — they query the screen size at call time so
they always reflect the current display resolution.

Functions
---------
get_screen_size()       → (width, height)
get_screen_center()     → (cx, cy)
get_top_left()          → (1, 1)          — avoids PyAutoGUI corner fail-safe
get_top_right()         → (w-2, 1)
get_bottom_left()       → (1, h-2)
get_bottom_right()      → (w-2, h-2)
get_top_center()        → (cx, 1)
get_bottom_center()     → (cx, h-2)
get_left_center()       → (1, cy)
get_right_center()      → (w-2, cy)
get_quarter(n)          → center of screen quadrant 1-4
get_window_center(title)→ center of a named window (or screen center fallback)
offset_from_center(dx, dy) → (cx+dx, cy+dy) clamped to screen
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Margin kept from screen edges to avoid triggering PyAutoGUI corner fail-safe
_EDGE_MARGIN = 2


def get_screen_size() -> Tuple[int, int]:
    """Return (width, height) of the primary monitor."""
    try:
        import pyautogui
        return pyautogui.size()
    except Exception:
        return (1920, 1080)   # safe fallback


def get_screen_center() -> Tuple[int, int]:
    """Return the pixel coordinates of the screen centre."""
    w, h = get_screen_size()
    return (w // 2, h // 2)


def get_top_left() -> Tuple[int, int]:
    """Top-left corner with edge margin (avoids fail-safe trigger)."""
    return (_EDGE_MARGIN, _EDGE_MARGIN)


def get_top_right() -> Tuple[int, int]:
    w, _ = get_screen_size()
    return (w - _EDGE_MARGIN, _EDGE_MARGIN)


def get_bottom_left() -> Tuple[int, int]:
    _, h = get_screen_size()
    return (_EDGE_MARGIN, h - _EDGE_MARGIN)


def get_bottom_right() -> Tuple[int, int]:
    w, h = get_screen_size()
    return (w - _EDGE_MARGIN, h - _EDGE_MARGIN)


def get_top_center() -> Tuple[int, int]:
    w, _ = get_screen_size()
    return (w // 2, _EDGE_MARGIN)


def get_bottom_center() -> Tuple[int, int]:
    w, h = get_screen_size()
    return (w // 2, h - _EDGE_MARGIN)


def get_left_center() -> Tuple[int, int]:
    _, h = get_screen_size()
    return (_EDGE_MARGIN, h // 2)


def get_right_center() -> Tuple[int, int]:
    w, h = get_screen_size()
    return (w - _EDGE_MARGIN, h // 2)


def get_quarter(n: int) -> Tuple[int, int]:
    """
    Return the centre of screen quadrant n (1=top-left, 2=top-right,
    3=bottom-left, 4=bottom-right).
    """
    w, h = get_screen_size()
    qw, qh = w // 2, h // 2
    mapping = {
        1: (qw // 2,          qh // 2),
        2: (qw + qw // 2,     qh // 2),
        3: (qw // 2,          qh + qh // 2),
        4: (qw + qw // 2,     qh + qh // 2),
    }
    return mapping.get(n, get_screen_center())


def get_window_center(title: str) -> Tuple[int, int]:
    """
    Return the centre pixel of the first window whose title contains `title`.
    Falls back to screen centre if the window is not found.
    """
    try:
        import pygetwindow as gw
        for win in gw.getAllWindows():
            if win.title and title.lower() in win.title.lower():
                cx = win.left + win.width  // 2
                cy = win.top  + win.height // 2
                logger.debug(f"coordinate_utils: window {win.title!r} centre = ({cx},{cy})")
                return (cx, cy)
    except Exception as exc:
        logger.debug(f"coordinate_utils: get_window_center failed: {exc}")
    return get_screen_center()


def offset_from_center(dx: int = 0, dy: int = 0) -> Tuple[int, int]:
    """
    Return screen-centre + (dx, dy), clamped to screen bounds.
    Useful for relative positioning: "move 200px right of centre".
    """
    cx, cy = get_screen_center()
    w, h   = get_screen_size()
    x = max(_EDGE_MARGIN, min(cx + dx, w - _EDGE_MARGIN))
    y = max(_EDGE_MARGIN, min(cy + dy, h - _EDGE_MARGIN))
    return (x, y)


def clamp(x: int, y: int) -> Tuple[int, int]:
    """Clamp arbitrary coordinates to safe screen bounds."""
    w, h = get_screen_size()
    return (
        max(_EDGE_MARGIN, min(x, w - _EDGE_MARGIN)),
        max(_EDGE_MARGIN, min(y, h - _EDGE_MARGIN)),
    )
