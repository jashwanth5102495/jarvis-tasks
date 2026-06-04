"""
app_registry.py
===============
Dynamic application alias registry for JARVIS.

Separates "what the user says" from "what executable to run",
so the AppController never needs to be modified to support new apps.

Structure
---------
APP_REGISTRY : Dict[canonical_name → AppEntry]

AppEntry contains:
  - aliases     : list of strings the user might say (all lowercase)
  - executable  : Windows executable name or full path
  - fallback_cmd: alternative launch command if executable not found
  - description : human-readable description

Public API
----------
resolve(user_input)  → (canonical_name, executable) or (None, None)
get_executable(name) → str or None
list_apps()          → List[str]   (canonical names)
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AppEntry:
    canonical:    str
    executable:   str
    aliases:      List[str]        = field(default_factory=list)
    fallback_cmd: Optional[str]    = None
    description:  str              = ""


# ─────────────────────────────────────────────────────────────────────────────
# Master registry
# ─────────────────────────────────────────────────────────────────────────────
# All alias strings must be lowercase.
# executable is the .exe name (Windows PATH) or full path string.

_REGISTRY_DATA: List[AppEntry] = [

    # ── Browsers ──────────────────────────────────────────────────────────────
    AppEntry(
        canonical="chrome",
        executable="chrome.exe",
        aliases=["chrome", "google chrome", "chromium"],
        fallback_cmd="start chrome",
        description="Google Chrome browser",
    ),
    AppEntry(
        canonical="brave",
        executable="brave.exe",
        aliases=["brave", "brave browser", "bravebrowser"],
        fallback_cmd="start brave",
        description="Brave browser",
    ),
    AppEntry(
        canonical="firefox",
        executable="firefox.exe",
        aliases=["firefox", "mozilla", "mozilla firefox", "ff"],
        fallback_cmd="start firefox",
        description="Mozilla Firefox browser",
    ),
    AppEntry(
        canonical="edge",
        executable="msedge.exe",
        aliases=["edge", "microsoft edge", "ms edge"],
        fallback_cmd="start msedge",
        description="Microsoft Edge browser",
    ),
    AppEntry(
        canonical="opera",
        executable="opera.exe",
        aliases=["opera", "opera browser"],
        fallback_cmd="start opera",
        description="Opera browser",
    ),

    # ── Editors & IDEs ────────────────────────────────────────────────────────
    AppEntry(
        canonical="vscode",
        executable="code",
        aliases=["vscode", "vs code", "visual studio code", "code", "vscodium"],
        fallback_cmd="code",
        description="Visual Studio Code",
    ),
    AppEntry(
        canonical="notepad",
        executable="notepad.exe",
        aliases=["notepad", "text editor", "notepad++"],
        description="Notepad text editor",
    ),
    AppEntry(
        canonical="notepadpp",
        executable="notepad++.exe",
        aliases=["notepad plus", "notepad plus plus", "notepad++"],
        description="Notepad++ text editor",
    ),
    AppEntry(
        canonical="sublime",
        executable="sublime_text.exe",
        aliases=["sublime", "sublime text"],
        description="Sublime Text editor",
    ),

    # ── Communication ─────────────────────────────────────────────────────────
    AppEntry(
        canonical="discord",
        executable="discord.exe",
        aliases=["discord"],
        fallback_cmd="start discord",
        description="Discord messaging",
    ),
    AppEntry(
        canonical="telegram",
        executable="telegram.exe",
        aliases=["telegram", "telegram desktop"],
        fallback_cmd="start telegram",
        description="Telegram messenger",
    ),
    AppEntry(
        canonical="whatsapp",
        executable="whatsapp.exe",
        aliases=["whatsapp", "whats app"],
        description="WhatsApp desktop",
    ),
    AppEntry(
        canonical="slack",
        executable="slack.exe",
        aliases=["slack"],
        fallback_cmd="start slack",
        description="Slack messaging",
    ),
    AppEntry(
        canonical="zoom",
        executable="zoom.exe",
        aliases=["zoom", "zoom meetings"],
        description="Zoom video calls",
    ),
    AppEntry(
        canonical="teams",
        executable="teams.exe",
        aliases=["teams", "microsoft teams", "ms teams"],
        description="Microsoft Teams",
    ),
    AppEntry(
        canonical="outlook",
        executable="outlook.exe",
        aliases=["outlook", "microsoft outlook"],
        description="Microsoft Outlook",
    ),

    # ── Music & Media ─────────────────────────────────────────────────────────
    AppEntry(
        canonical="spotify",
        executable="spotify.exe",
        aliases=["spotify", "spotify music"],
        fallback_cmd="start spotify",
        description="Spotify music player",
    ),
    AppEntry(
        canonical="vlc",
        executable="vlc.exe",
        aliases=["vlc", "vlc media player", "videolan"],
        description="VLC media player",
    ),
    AppEntry(
        canonical="itunes",
        executable="itunes.exe",
        aliases=["itunes", "apple music"],
        description="iTunes / Apple Music",
    ),

    # ── Gaming ────────────────────────────────────────────────────────────────
    AppEntry(
        canonical="steam",
        executable="steam.exe",
        aliases=["steam", "steam client"],
        fallback_cmd="start steam",
        description="Steam gaming platform",
    ),
    AppEntry(
        canonical="epicgames",
        executable="epicgameslauncher.exe",
        aliases=["epic games", "epic", "epic launcher", "epic games launcher"],
        description="Epic Games Launcher",
    ),

    # ── Productivity ──────────────────────────────────────────────────────────
    AppEntry(
        canonical="word",
        executable="winword.exe",
        aliases=["word", "microsoft word", "ms word"],
        description="Microsoft Word",
    ),
    AppEntry(
        canonical="excel",
        executable="excel.exe",
        aliases=["excel", "microsoft excel", "ms excel"],
        description="Microsoft Excel",
    ),
    AppEntry(
        canonical="powerpoint",
        executable="powerpnt.exe",
        aliases=["powerpoint", "microsoft powerpoint", "ppt"],
        description="Microsoft PowerPoint",
    ),

    # ── System ────────────────────────────────────────────────────────────────
    AppEntry(
        canonical="explorer",
        executable="explorer.exe",
        aliases=["explorer", "file explorer", "windows explorer", "files"],
        description="Windows File Explorer",
    ),
    AppEntry(
        canonical="calculator",
        executable="calc.exe",
        aliases=["calculator", "calc"],
        description="Windows Calculator",
    ),
    AppEntry(
        canonical="paint",
        executable="mspaint.exe",
        aliases=["paint", "ms paint", "microsoft paint"],
        description="Microsoft Paint",
    ),
    AppEntry(
        canonical="cmd",
        executable="cmd.exe",
        aliases=["cmd", "command prompt", "command line", "dos"],
        description="Windows Command Prompt",
    ),
    AppEntry(
        canonical="powershell",
        executable="powershell.exe",
        aliases=["powershell", "ps", "pwsh"],
        description="Windows PowerShell",
    ),
    AppEntry(
        canonical="terminal",
        executable="wt.exe",
        aliases=["terminal", "windows terminal", "wt"],
        description="Windows Terminal",
    ),

    # ── Design ────────────────────────────────────────────────────────────────
    AppEntry(
        canonical="photoshop",
        executable="photoshop.exe",
        aliases=["photoshop", "adobe photoshop", "ps"],
        description="Adobe Photoshop",
    ),
    AppEntry(
        canonical="figma",
        executable="figma.exe",
        aliases=["figma"],
        fallback_cmd="start https://figma.com",
        description="Figma design tool",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Registry class
# ─────────────────────────────────────────────────────────────────────────────

class AppRegistry:
    """
    Dynamic application alias registry.

    Usage
    -----
    canonical, exe = app_registry.resolve("Open Brave")
    # -> ("brave", "brave.exe")

    canonical, exe = app_registry.resolve("launch discord")
    # -> ("discord", "discord.exe")

    canonical, exe = app_registry.resolve("xyzzy")
    # -> (None, None)
    """

    def __init__(self, entries: List[AppEntry] = None) -> None:
        self._entries: Dict[str, AppEntry] = {}
        self._alias_map: Dict[str, str] = {}   # alias_lower -> canonical_name

        for entry in (entries or _REGISTRY_DATA):
            self._entries[entry.canonical] = entry
            for alias in entry.aliases:
                self._alias_map[alias.lower()] = entry.canonical

    # ── Public API ─────────────────────────────────────────────────────────────

    def resolve(self, user_input: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolve a free-form user string to (canonical_name, executable).

        Matching strategy (in order):
        1. Exact alias match
        2. Substring alias match (e.g. "chrome" inside "open google chrome")
        3. Returns (None, None) if nothing found

        Returns
        -------
        (canonical_name, executable) or (None, None)
        """
        text = user_input.lower().strip()

        # Strip common launch prefixes so "open chrome" → "chrome"
        for prefix in ("open ", "launch ", "start ", "run ", "close "):
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        # 1. Exact alias match
        if text in self._alias_map:
            return self._get_entry(self._alias_map[text])

        # 2. Substring match — longest alias that appears in the text wins
        best_alias: Optional[str] = None
        best_len = 0
        for alias, canonical in self._alias_map.items():
            if alias in text and len(alias) > best_len:
                best_alias = canonical
                best_len   = len(alias)

        if best_alias:
            return self._get_entry(best_alias)

        logger.debug(f"AppRegistry: no match for {user_input!r}")
        return (None, None)

    def get_executable(self, canonical: str) -> Optional[str]:
        entry = self._entries.get(canonical)
        return entry.executable if entry else None

    def get_entry(self, canonical: str) -> Optional[AppEntry]:
        return self._entries.get(canonical)

    def is_installed(self, canonical: str) -> bool:
        """Check if the executable is findable on the system PATH."""
        entry = self._entries.get(canonical)
        if not entry:
            return False
        return shutil.which(entry.executable) is not None

    def list_apps(self) -> List[str]:
        return sorted(self._entries.keys())

    def list_aliases(self) -> Dict[str, List[str]]:
        return {name: e.aliases for name, e in self._entries.items()}

    def register(self, entry: AppEntry) -> None:
        """Register a new app entry at runtime."""
        self._entries[entry.canonical] = entry
        for alias in entry.aliases:
            self._alias_map[alias.lower()] = entry.canonical
        logger.info(f"AppRegistry: registered {entry.canonical!r}")

    # ── Internal ───────────────────────────────────────────────────────────────

    def _get_entry(self, canonical: str) -> Tuple[str, str]:
        entry = self._entries[canonical]
        # Prefer executable from PATH; fall back to fallback_cmd
        exe = entry.executable
        if shutil.which(exe) is None and entry.fallback_cmd:
            exe = entry.fallback_cmd
        logger.debug(f"AppRegistry: resolved {canonical!r} -> {exe!r}")
        return (canonical, exe)


# Module-level singleton
app_registry = AppRegistry()
