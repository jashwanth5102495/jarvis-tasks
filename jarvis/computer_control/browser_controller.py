"""
browser_controller.py
=====================
BrowserController — desktop browser interaction via PyAutoGUI + webbrowser.

This is the Milestone 4 browser controller — it uses the OS default browser
and PyAutoGUI for interaction. Playwright/Selenium are future upgrades.

Supported actions
-----------------
open_url          : open a URL in the default browser
search_google     : open Google search for a query
search_bing       : open Bing search for a query
focus_browser     : bring the browser window to the foreground
type_in_address   : focus address bar (Ctrl+L) and type a URL
new_tab           : open a new browser tab (Ctrl+T)
close_tab         : close the current tab (Ctrl+W)
refresh_page      : refresh the current page (F5)
scroll_page       : scroll the browser page up/down
go_back           : navigate back (Alt+Left)
go_forward        : navigate forward (Alt+Right)

Future compatibility
--------------------
The interface is designed so Playwright/Selenium can replace the
PyAutoGUI implementation without changing the action API.
"""

from __future__ import annotations

import logging
import time
import webbrowser
from urllib.parse import quote_plus

from computer_control.cc_models import ActionRisk
from computer_control.failsafe import failsafe

logger = logging.getLogger(__name__)

_BROWSER_TITLES = ["chrome", "firefox", "edge", "browser", "mozilla", "chromium"]
_OPEN_DELAY_S   = 1.5   # wait after opening URL for browser to load


class BrowserController:
    """
    Controls the desktop browser via PyAutoGUI keyboard shortcuts
    and the webbrowser module.

    Usage
    -----
    browser_controller.open_url("https://google.com")
    browser_controller.search_google("latest AI models")
    browser_controller.new_tab()
    """

    SUPPORTED_ACTIONS = [
        "open_url", "search_google", "search_bing",
        "focus_browser", "type_in_address",
        "new_tab", "close_tab", "refresh_page",
        "scroll_page", "go_back", "go_forward",
    ]

    ACTION_RISK = {
        "open_url":        ActionRisk.HIGH,
        "search_google":   ActionRisk.HIGH,
        "search_bing":     ActionRisk.HIGH,
        "focus_browser":   ActionRisk.MEDIUM,
        "type_in_address": ActionRisk.HIGH,
        "new_tab":         ActionRisk.HIGH,
        "close_tab":       ActionRisk.HIGH,
        "refresh_page":    ActionRisk.MEDIUM,
        "scroll_page":     ActionRisk.MEDIUM,
        "go_back":         ActionRisk.MEDIUM,
        "go_forward":      ActionRisk.MEDIUM,
    }

    def __init__(self) -> None:
        try:
            import pyautogui
            self._pag = pyautogui
        except ImportError:
            raise ImportError("pyautogui is required for BrowserController.")

    # ── Public actions ─────────────────────────────────────────────────────────

    def open_url(self, url: str) -> str:
        failsafe.check()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        time.sleep(_OPEN_DELAY_S)
        logger.info(f"BrowserController: opened {url}")
        return f"Opened URL: {url}"

    def search_google(self, query: str) -> str:
        failsafe.check()
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(url)
        time.sleep(_OPEN_DELAY_S)
        logger.info(f"BrowserController: Google search for {query!r}")
        return f"Google search opened: {query!r}"

    def search_bing(self, query: str) -> str:
        failsafe.check()
        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        webbrowser.open(url)
        time.sleep(_OPEN_DELAY_S)
        logger.info(f"BrowserController: Bing search for {query!r}")
        return f"Bing search opened: {query!r}"

    def focus_browser(self) -> str:
        failsafe.check()
        try:
            import pygetwindow as gw
            for title_hint in _BROWSER_TITLES:
                for win in gw.getAllWindows():
                    if win.title and title_hint in win.title.lower():
                        win.activate()
                        time.sleep(0.3)
                        logger.info(f"BrowserController: focused {win.title!r}")
                        return f"Browser focused: {win.title!r}"
            return "No browser window found to focus"
        except Exception as exc:
            return f"Could not focus browser: {exc}"

    def type_in_address(self, url: str) -> str:
        """Focus address bar and type a URL."""
        failsafe.check()
        self._pag.hotkey("ctrl", "l")
        time.sleep(0.2)
        self._pag.hotkey("ctrl", "a")
        time.sleep(0.1)
        self._pag.typewrite(url, interval=0.03)
        self._pag.press("enter")
        time.sleep(_OPEN_DELAY_S)
        logger.info(f"BrowserController: typed address {url!r}")
        return f"Navigated to: {url}"

    def new_tab(self) -> str:
        failsafe.check()
        self._pag.hotkey("ctrl", "t")
        time.sleep(0.3)
        logger.info("BrowserController: new tab opened")
        return "New tab opened"

    def close_tab(self) -> str:
        failsafe.check()
        self._pag.hotkey("ctrl", "w")
        time.sleep(0.2)
        logger.info("BrowserController: tab closed")
        return "Tab closed"

    def refresh_page(self) -> str:
        failsafe.check()
        self._pag.press("f5")
        time.sleep(0.5)
        logger.info("BrowserController: page refreshed")
        return "Page refreshed"

    def scroll_page(self, clicks: int = 3) -> str:
        failsafe.check()
        self._pag.scroll(clicks)
        direction = "down" if clicks < 0 else "up"
        logger.info(f"BrowserController: scrolled {abs(clicks)} clicks {direction}")
        return f"Scrolled {abs(clicks)} clicks {direction}"

    def go_back(self) -> str:
        failsafe.check()
        self._pag.hotkey("alt", "left")
        time.sleep(0.3)
        logger.info("BrowserController: navigated back")
        return "Navigated back"

    def go_forward(self) -> str:
        failsafe.check()
        self._pag.hotkey("alt", "right")
        time.sleep(0.3)
        logger.info("BrowserController: navigated forward")
        return "Navigated forward"

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"BrowserController: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)
