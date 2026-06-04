
"""
ui_theme_manager.py
===================
Theme management for JARVIS cinematic overlay.
Provides configurable color schemes and visual presets.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict

logger = logging.getLogger(__name__)


class UITheme(Enum):
    CINEMATIC_BLUE = "cinematic_blue"
    STEALTH_DARK = "stealth_dark"
    HOLOGRAPHIC_CYAN = "holographic_cyan"
    MINIMAL_WHITE = "minimal_white"
    JARVIS_CLASSIC = "jarvis_classic"


@dataclass
class ThemeColors:
    background: str
    foreground: str
    active: str
    paused: str
    listening: str
    speaking: str
    executing: str
    thinking: str
    error: str
    recovering: str
    glow: str


class UIThemeManager:
    _themes: Dict[UITheme, ThemeColors] = {
        UITheme.CINEMATIC_BLUE: ThemeColors(
            background="transparent",
            foreground="#ffffff",
            active="#00aaff",
            paused="#666666",
            listening="#0088ff",
            speaking="#00ccff",
            executing="#88cc00",
            thinking="#ffaa00",
            error="#ff4444",
            recovering="#ff8800",
            glow="#00aaff"
        ),
        UITheme.STEALTH_DARK: ThemeColors(
            background="transparent",
            foreground="#88ff88",
            active="#00ff88",
            paused="#444444",
            listening="#00ffaa",
            speaking="#00ffff",
            executing="#88ff00",
            thinking="#ffcc00",
            error="#ff0044",
            recovering="#ff6600",
            glow="#00ff88"
        ),
        UITheme.HOLOGRAPHIC_CYAN: ThemeColors(
            background="transparent",
            foreground="#00ffff",
            active="#00ffff",
            paused="#004444",
            listening="#00ccff",
            speaking="#00ffcc",
            executing="#00ff88",
            thinking="#ffcc00",
            error="#ff4400",
            recovering="#ff8800",
            glow="#00ffff"
        ),
        UITheme.MINIMAL_WHITE: ThemeColors(
            background="transparent",
            foreground="#000000",
            active="#0066cc",
            paused="#999999",
            listening="#0088dd",
            speaking="#00aaff",
            executing="#44aa00",
            thinking="#cc8800",
            error="#cc0000",
            recovering="#cc6600",
            glow="#0066cc"
        ),
        UITheme.JARVIS_CLASSIC: ThemeColors(
            background="transparent",
            foreground="#ffd700",
            active="#ffd700",
            paused="#665500",
            listening="#ffcc00",
            speaking="#ffee00",
            executing="#aaff00",
            thinking="#ff9900",
            error="#ff4444",
            recovering="#ff8844",
            glow="#ffd700"
        )
    }

    def __init__(self):
        self._current_theme: UITheme = UITheme.CINEMATIC_BLUE
        logger.info(f"UI Theme Manager initialized with theme: {self._current_theme.value}")

    @property
    def current_theme(self) -> UITheme:
        return self._current_theme

    @current_theme.setter
    def current_theme(self, theme: UITheme):
        self._current_theme = theme
        logger.info(f"Theme changed to: {theme.value}")

    @property
    def colors(self) -> ThemeColors:
        return self._themes[self._current_theme]

    def get_theme_colors(self, theme: UITheme) -> ThemeColors:
        return self._themes.get(theme, self._themes[UITheme.CINEMATIC_BLUE])


ui_theme_manager = UIThemeManager()

