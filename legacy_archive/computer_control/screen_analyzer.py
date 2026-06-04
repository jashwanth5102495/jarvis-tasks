"""
screen_analyzer.py
==================
ScreenAnalyzer — lightweight screen state inspection.

Capabilities
------------
get_screen_info    : screen resolution, color depth (SAFE)
get_pixel_color    : color of a pixel at (x, y) (SAFE)
detect_windows     : list visible window titles (SAFE)
analyze_screenshot : basic analysis of a saved screenshot
                     (dimensions, dominant colors, file size)
compare_screenshots: pixel-difference between two screenshots

This module is intentionally lightweight for Milestone 4.
It prepares the architecture for future vision-based AI control
(GPT-4V, Claude Vision, local LLMs) without implementing it yet.

Future extension points
-----------------------
- add_analyzer(name, fn): register a custom analysis function
- The analyze_screenshot method returns a dict that future
  vision models can extend with semantic descriptions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from computer_control.failsafe import failsafe

logger = logging.getLogger(__name__)


class ScreenAnalyzer:
    """
    Inspects screen state and analyzes screenshots.

    Usage
    -----
    info = screen_analyzer.get_screen_info()
    color = screen_analyzer.get_pixel_color(500, 300)
    analysis = screen_analyzer.analyze_screenshot("path/to/shot.png")
    """

    SUPPORTED_ACTIONS = [
        "get_screen_info", "get_pixel_color", "detect_windows",
        "analyze_screenshot", "compare_screenshots",
    ]

    def __init__(self) -> None:
        # Extension point: custom analyzers registered at runtime
        self._custom_analyzers: Dict[str, Callable] = {}

    # ── Public actions ─────────────────────────────────────────────────────────

    def get_screen_info(self) -> str:
        failsafe.check()
        try:
            import pyautogui
            w, h = pyautogui.size()
            logger.info(f"ScreenAnalyzer: screen size = {w}×{h}")
            return f"Screen: {w}×{h} pixels"
        except Exception as exc:
            return f"Could not get screen info: {exc}"

    def get_pixel_color(self, x: int, y: int) -> str:
        failsafe.check()
        try:
            import pyautogui
            x, y = failsafe.clamp_to_screen(x, y)
            color = pyautogui.pixel(x, y)
            logger.info(f"ScreenAnalyzer: pixel ({x},{y}) = RGB{color}")
            return f"Pixel ({x},{y}): RGB{color}"
        except Exception as exc:
            return f"Could not get pixel color: {exc}"

    def detect_windows(self) -> str:
        failsafe.check()
        try:
            import pygetwindow as gw
            titles = [t for t in gw.getAllTitles() if t.strip()]
            unique = sorted(set(titles))[:20]
            result = "\n".join(f"  • {t}" for t in unique)
            logger.info(f"ScreenAnalyzer: detected {len(unique)} windows")
            return f"Visible windows ({len(unique)}):\n{result}"
        except Exception as exc:
            return f"Could not detect windows: {exc}"

    def analyze_screenshot(self, screenshot_path: str) -> str:
        """
        Basic analysis of a saved screenshot.
        Returns dimensions, file size, and dominant color info.
        """
        path = Path(screenshot_path)
        if not path.exists():
            return f"Screenshot not found: {screenshot_path}"
        try:
            from PIL import Image
            img  = Image.open(path)
            w, h = img.size
            size_kb = path.stat().st_size // 1024

            # Sample dominant colors (5×5 grid of pixels)
            colors = []
            step_x, step_y = w // 5, h // 5
            rgb_img = img.convert("RGB")
            for row in range(5):
                for col in range(5):
                    px = rgb_img.getpixel((col * step_x, row * step_y))
                    colors.append(px)

            avg_r = sum(c[0] for c in colors) // len(colors)
            avg_g = sum(c[1] for c in colors) // len(colors)
            avg_b = sum(c[2] for c in colors) // len(colors)

            result = (
                f"Screenshot: {path.name}\n"
                f"  Dimensions : {w}×{h} px\n"
                f"  File size  : {size_kb} KB\n"
                f"  Avg color  : RGB({avg_r}, {avg_g}, {avg_b})\n"
                f"  Mode       : {img.mode}"
            )

            # Run any registered custom analyzers
            for name, fn in self._custom_analyzers.items():
                try:
                    extra = fn(img, path)
                    result += f"\n  [{name}]: {extra}"
                except Exception as exc:
                    result += f"\n  [{name}]: error — {exc}"

            logger.info(f"ScreenAnalyzer: analyzed {path.name}")
            return result

        except Exception as exc:
            return f"Analysis failed: {exc}"

    def compare_screenshots(
        self,
        path_a: str,
        path_b: str,
    ) -> str:
        """
        Compute pixel-level difference between two screenshots.
        Returns a similarity percentage.
        """
        try:
            import cv2
            import numpy as np

            img_a = cv2.imread(path_a)
            img_b = cv2.imread(path_b)

            if img_a is None or img_b is None:
                return "Could not load one or both screenshots"

            # Resize to same dimensions for comparison
            h = min(img_a.shape[0], img_b.shape[0])
            w = min(img_a.shape[1], img_b.shape[1])
            img_a = cv2.resize(img_a, (w, h))
            img_b = cv2.resize(img_b, (w, h))

            diff       = cv2.absdiff(img_a, img_b)
            total_px   = w * h * 3
            diff_sum   = int(np.sum(diff))
            similarity = max(0.0, 1.0 - diff_sum / (total_px * 255)) * 100

            logger.info(f"ScreenAnalyzer: similarity = {similarity:.1f}%")
            return f"Screenshot similarity: {similarity:.1f}%"

        except Exception as exc:
            return f"Comparison failed: {exc}"

    # ── Extension point ────────────────────────────────────────────────────────

    def add_analyzer(self, name: str, fn: Callable) -> None:
        """Register a custom analysis function for analyze_screenshot."""
        self._custom_analyzers[name] = fn
        logger.info(f"ScreenAnalyzer: registered custom analyzer {name!r}")

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"ScreenAnalyzer: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)


# Module-level singleton
screen_analyzer = ScreenAnalyzer()
