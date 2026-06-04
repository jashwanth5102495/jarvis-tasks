"""
action_translator.py
====================
Semantic Intent → Executable Controller Action Translation Layer.

This is the FINAL execution bridge between the planner's semantic
workflow descriptions and the low-level controller methods.

Pipeline
--------
  Natural language intent  (e.g. "move_to_center")
       ↓
  ActionTranslator.translate(semantic_action, raw_params)
       ↓
  TranslatedAction(controller, method, resolved_params)
       ↓
  ControlManager._dispatch(action)
       ↓
  MouseController.move_to(x=960, y=540)   ← actual execution

Semantic action naming convention
----------------------------------
Semantic actions use snake_case descriptive names:
  "move_to_center"        → mouse.move_to(x=cx, y=cy)
  "right_click"           → mouse.right_click()
  "scroll_down"           → mouse.scroll(clicks=-3)
  "press_enter"           → keyboard.press(key="enter")
  "save_shortcut"         → keyboard.hotkey("ctrl", "s")
  "open_chrome"           → app.open_app(app_name="chrome")
  "search_google"         → browser.search_google(query=...)
  "take_screenshot"       → screenshot.capture_screen()

Adding new mappings
-------------------
1. Add entry to the appropriate SEMANTIC_* dict below.
2. If the action needs dynamic params (e.g. screen coordinates),
   add a resolver in _PARAM_RESOLVERS.
3. Done — no other files need changing.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from computer_control.cc_models import ActionRisk, ControlAction, ControllerType
from computer_control.coordinate_utils import (
    get_bottom_center, get_bottom_left, get_bottom_right,
    get_left_center, get_quarter, get_right_center,
    get_screen_center, get_screen_size,
    get_top_center, get_top_left, get_top_right,
    get_window_center, offset_from_center,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# TranslatedAction — result of a successful translation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TranslatedAction:
    """
    The resolved, executable form of a semantic action.

    Fields
    ------
    semantic_name : original semantic intent string
    controller    : ControllerType enum value
    method        : exact method name on the controller
    params        : fully resolved parameters ready for execution
    risk          : ActionRisk level
    description   : human-readable label for the UI
    """
    semantic_name: str
    controller:    ControllerType
    method:        str
    params:        Dict[str, Any]  = field(default_factory=dict)
    risk:          ActionRisk      = ActionRisk.MEDIUM
    description:   str             = ""

    def to_control_action(self) -> ControlAction:
        """Convert to a ControlAction ready for ControlManager.execute_actions()."""
        return ControlAction(
            controller  = self.controller,
            action      = self.method,
            params      = self.params,
            risk        = self.risk,
            description = self.description or f"{self.controller.value}.{self.method}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Semantic → (controller, method, risk) mapping tables
# ─────────────────────────────────────────────────────────────────────────────

# Each entry: semantic_name → (ControllerType, method_name, ActionRisk)
_SEMANTIC_MAP: Dict[str, Tuple[ControllerType, str, ActionRisk]] = {

    # ── Mouse ──────────────────────────────────────────────────────────────────
    "move_to_center":       (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_top_left":     (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_top_right":    (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_bottom_left":  (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_bottom_right": (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_top_center":   (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_bottom_center":(ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_left_center":  (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_right_center": (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_quarter_1":    (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_quarter_2":    (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_quarter_3":    (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to_quarter_4":    (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "move_to":              (ControllerType.MOUSE, "move_to",      ActionRisk.MEDIUM),
    "left_click":           (ControllerType.MOUSE, "click",        ActionRisk.HIGH),
    "click":                (ControllerType.MOUSE, "click",        ActionRisk.HIGH),
    "right_click":          (ControllerType.MOUSE, "right_click",  ActionRisk.HIGH),
    "double_click":         (ControllerType.MOUSE, "double_click", ActionRisk.HIGH),
    "scroll_up":            (ControllerType.MOUSE, "scroll",       ActionRisk.MEDIUM),
    "scroll_down":          (ControllerType.MOUSE, "scroll",       ActionRisk.MEDIUM),
    "scroll":               (ControllerType.MOUSE, "scroll",       ActionRisk.MEDIUM),
    "drag_to":              (ControllerType.MOUSE, "drag_to",      ActionRisk.HIGH),
    "get_mouse_position":   (ControllerType.MOUSE, "get_position", ActionRisk.SAFE),

    # ── Keyboard ───────────────────────────────────────────────────────────────
    "type_text":            (ControllerType.KEYBOARD, "type_text",   ActionRisk.HIGH),
    "type":                 (ControllerType.KEYBOARD, "type_text",   ActionRisk.HIGH),
    "press_enter":          (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_tab":            (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_escape":         (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_space":          (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_backspace":      (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_delete":         (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_up":             (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_down":           (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_left":           (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_right":          (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press_key":            (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "press":                (ControllerType.KEYBOARD, "press",       ActionRisk.HIGH),
    "save_shortcut":        (ControllerType.KEYBOARD, "hotkey",      ActionRisk.HIGH),
    "copy_shortcut":        (ControllerType.KEYBOARD, "hotkey",      ActionRisk.HIGH),
    "paste_shortcut":       (ControllerType.KEYBOARD, "hotkey",      ActionRisk.HIGH),
    "undo_shortcut":        (ControllerType.KEYBOARD, "hotkey",      ActionRisk.HIGH),
    "redo_shortcut":        (ControllerType.KEYBOARD, "hotkey",      ActionRisk.HIGH),
    "select_all":           (ControllerType.KEYBOARD, "hotkey",      ActionRisk.HIGH),
    "hotkey":               (ControllerType.KEYBOARD, "hotkey",      ActionRisk.HIGH),
    "clear_field":          (ControllerType.KEYBOARD, "clear_field", ActionRisk.HIGH),

    # ── Browser ────────────────────────────────────────────────────────────────
    "open_url":             (ControllerType.BROWSER, "open_url",        ActionRisk.HIGH),
    "open_website":         (ControllerType.BROWSER, "open_url",        ActionRisk.HIGH),
    "search_google":        (ControllerType.BROWSER, "search_google",   ActionRisk.HIGH),
    "google_search":        (ControllerType.BROWSER, "search_google",   ActionRisk.HIGH),
    "search_bing":          (ControllerType.BROWSER, "search_bing",     ActionRisk.HIGH),
    "bing_search":          (ControllerType.BROWSER, "search_bing",     ActionRisk.HIGH),
    "focus_browser":        (ControllerType.BROWSER, "focus_browser",   ActionRisk.MEDIUM),
    "new_tab":              (ControllerType.BROWSER, "new_tab",         ActionRisk.HIGH),
    "close_tab":            (ControllerType.BROWSER, "close_tab",       ActionRisk.HIGH),
    "refresh_page":         (ControllerType.BROWSER, "refresh_page",    ActionRisk.MEDIUM),
    "scroll_page_up":       (ControllerType.BROWSER, "scroll_page",     ActionRisk.MEDIUM),
    "scroll_page_down":     (ControllerType.BROWSER, "scroll_page",     ActionRisk.MEDIUM),
    "go_back":              (ControllerType.BROWSER, "go_back",         ActionRisk.MEDIUM),
    "go_forward":           (ControllerType.BROWSER, "go_forward",      ActionRisk.MEDIUM),
    "navigate_to":          (ControllerType.BROWSER, "type_in_address", ActionRisk.HIGH),

    # ── App ────────────────────────────────────────────────────────────────────
    "open_app":             (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "launch_app":           (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_chrome":          (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_firefox":         (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_edge":            (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_brave":           (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_opera":           (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_notepad":         (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_calculator":      (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_vscode":          (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_vs_code":         (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_paint":           (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_discord":         (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_spotify":         (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_telegram":        (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_slack":           (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_steam":           (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_word":            (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_excel":           (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_powerpoint":      (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_outlook":         (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "open_explorer":        (ControllerType.APP, "open_app",     ActionRisk.HIGH),
    "close_app":            (ControllerType.APP, "close_app",    ActionRisk.HIGH),
    "is_app_running":       (ControllerType.APP, "is_running",   ActionRisk.SAFE),
    "list_running_apps":    (ControllerType.APP, "list_running", ActionRisk.SAFE),
    "wait_for_app":         (ControllerType.APP, "wait_for_app", ActionRisk.SAFE),

    # ── Window ─────────────────────────────────────────────────────────────────
    "list_windows":         (ControllerType.WINDOW, "list_windows",      ActionRisk.SAFE),
    "focus_window":         (ControllerType.WINDOW, "focus_window",      ActionRisk.MEDIUM),
    "maximize_window":      (ControllerType.WINDOW, "maximize_window",   ActionRisk.MEDIUM),
    "minimize_window":      (ControllerType.WINDOW, "minimize_window",   ActionRisk.MEDIUM),
    "get_active_window":    (ControllerType.WINDOW, "get_active_window", ActionRisk.SAFE),
    "close_window":         (ControllerType.WINDOW, "close_window",      ActionRisk.HIGH),
    "window_exists":        (ControllerType.WINDOW, "window_exists",     ActionRisk.SAFE),

    # ── Screenshot ─────────────────────────────────────────────────────────────
    "take_screenshot":      (ControllerType.SCREENSHOT, "capture_screen",  ActionRisk.SAFE),
    "capture_screen":       (ControllerType.SCREENSHOT, "capture_screen",  ActionRisk.SAFE),
    "capture_region":       (ControllerType.SCREENSHOT, "capture_region",  ActionRisk.SAFE),
    "get_latest_screenshot":(ControllerType.SCREENSHOT, "get_latest",      ActionRisk.SAFE),
    "list_screenshots":     (ControllerType.SCREENSHOT, "list_screenshots",ActionRisk.SAFE),

    # ── Screen ─────────────────────────────────────────────────────────────────
    "get_screen_info":      (ControllerType.SCREEN, "get_screen_info",    ActionRisk.SAFE),
    "get_pixel_color":      (ControllerType.SCREEN, "get_pixel_color",    ActionRisk.SAFE),
    "detect_windows":       (ControllerType.SCREEN, "detect_windows",     ActionRisk.SAFE),
    "analyze_screenshot":   (ControllerType.SCREEN, "analyze_screenshot", ActionRisk.SAFE),

    # ── UI Locator ─────────────────────────────────────────────────────────────
    "locate_image":         (ControllerType.UI, "locate_image",      ActionRisk.SAFE),
    "locate_and_click":     (ControllerType.UI, "locate_and_click",  ActionRisk.HIGH),
    "wait_for_image":       (ControllerType.UI, "wait_for_image",    ActionRisk.SAFE),
    "image_exists":         (ControllerType.UI, "image_exists",      ActionRisk.SAFE),
}


# ─────────────────────────────────────────────────────────────────────────────
# Parameter resolvers — inject dynamic params for semantic actions
# ─────────────────────────────────────────────────────────────────────────────
# Each resolver: (semantic_name, raw_params) → resolved_params dict

def _resolve_move_to_center(raw: dict) -> dict:
    x, y = get_screen_center()
    return {"x": x, "y": y, **{k: v for k, v in raw.items() if k not in ("x", "y")}}

def _resolve_move_to_top_left(raw: dict) -> dict:
    x, y = get_top_left()
    return {"x": x, "y": y}

def _resolve_move_to_top_right(raw: dict) -> dict:
    x, y = get_top_right()
    return {"x": x, "y": y}

def _resolve_move_to_bottom_left(raw: dict) -> dict:
    x, y = get_bottom_left()
    return {"x": x, "y": y}

def _resolve_move_to_bottom_right(raw: dict) -> dict:
    x, y = get_bottom_right()
    return {"x": x, "y": y}

def _resolve_move_to_top_center(raw: dict) -> dict:
    x, y = get_top_center()
    return {"x": x, "y": y}

def _resolve_move_to_bottom_center(raw: dict) -> dict:
    x, y = get_bottom_center()
    return {"x": x, "y": y}

def _resolve_move_to_left_center(raw: dict) -> dict:
    x, y = get_left_center()
    return {"x": x, "y": y}

def _resolve_move_to_right_center(raw: dict) -> dict:
    x, y = get_right_center()
    return {"x": x, "y": y}

def _resolve_quarter(n: int) -> Callable[[dict], dict]:
    def _r(raw: dict) -> dict:
        x, y = get_quarter(n)
        return {"x": x, "y": y}
    return _r

def _resolve_scroll_down(raw: dict) -> dict:
    clicks = -abs(raw.get("clicks", 3))
    return {"clicks": clicks}

def _resolve_scroll_up(raw: dict) -> dict:
    clicks = abs(raw.get("clicks", 3))
    return {"clicks": clicks}

def _resolve_scroll_page_down(raw: dict) -> dict:
    return {"clicks": -raw.get("clicks", 3)}

def _resolve_scroll_page_up(raw: dict) -> dict:
    return {"clicks": raw.get("clicks", 3)}

def _resolve_press_enter(raw: dict) -> dict:
    return {"key": "enter"}

def _resolve_press_tab(raw: dict) -> dict:
    return {"key": "tab"}

def _resolve_press_escape(raw: dict) -> dict:
    return {"key": "escape"}

def _resolve_press_space(raw: dict) -> dict:
    return {"key": "space"}

def _resolve_press_backspace(raw: dict) -> dict:
    return {"key": "backspace"}

def _resolve_press_delete(raw: dict) -> dict:
    return {"key": "delete"}

def _resolve_press_up(raw: dict) -> dict:
    return {"key": "up"}

def _resolve_press_down(raw: dict) -> dict:
    return {"key": "down"}

def _resolve_press_left(raw: dict) -> dict:
    return {"key": "left"}

def _resolve_press_right(raw: dict) -> dict:
    return {"key": "right"}

def _resolve_save_shortcut(raw: dict) -> dict:
    return {}   # hotkey(*keys) — keys passed as positional args via special handling

def _resolve_copy_shortcut(raw: dict) -> dict:
    return {}

def _resolve_paste_shortcut(raw: dict) -> dict:
    return {}

def _resolve_undo_shortcut(raw: dict) -> dict:
    return {}

def _resolve_redo_shortcut(raw: dict) -> dict:
    return {}

def _resolve_select_all(raw: dict) -> dict:
    return {}

def _resolve_open_chrome(raw: dict) -> dict:
    return {"app_name": "chrome"}

def _resolve_open_firefox(raw: dict) -> dict:
    return {"app_name": "firefox"}

def _resolve_open_edge(raw: dict) -> dict:
    return {"app_name": "edge"}

def _resolve_open_brave(raw: dict) -> dict:
    return {"app_name": "brave"}

def _resolve_open_opera(raw: dict) -> dict:
    return {"app_name": "opera"}

def _resolve_open_notepad(raw: dict) -> dict:
    return {"app_name": "notepad"}

def _resolve_open_calculator(raw: dict) -> dict:
    return {"app_name": "calculator"}

def _resolve_open_vscode(raw: dict) -> dict:
    return {"app_name": "vscode"}

def _resolve_open_vs_code(raw: dict) -> dict:
    return {"app_name": "vscode"}

def _resolve_open_paint(raw: dict) -> dict:
    return {"app_name": "paint"}

def _resolve_open_discord(raw: dict) -> dict:
    return {"app_name": "discord"}

def _resolve_open_spotify(raw: dict) -> dict:
    return {"app_name": "spotify"}

def _resolve_open_telegram(raw: dict) -> dict:
    return {"app_name": "telegram"}

def _resolve_open_slack(raw: dict) -> dict:
    return {"app_name": "slack"}

def _resolve_open_steam(raw: dict) -> dict:
    return {"app_name": "steam"}

def _resolve_open_word(raw: dict) -> dict:
    return {"app_name": "word"}

def _resolve_open_excel(raw: dict) -> dict:
    return {"app_name": "excel"}

def _resolve_open_powerpoint(raw: dict) -> dict:
    return {"app_name": "powerpoint"}

def _resolve_open_outlook(raw: dict) -> dict:
    return {"app_name": "outlook"}

def _resolve_open_explorer(raw: dict) -> dict:
    return {"app_name": "explorer"}

def _resolve_take_screenshot(raw: dict) -> dict:
    return {"suffix": raw.get("suffix", "jarvis")}


# Maps semantic_name → resolver function
_PARAM_RESOLVERS: Dict[str, Callable[[dict], dict]] = {
    "move_to_center":        _resolve_move_to_center,
    "move_to_top_left":      _resolve_move_to_top_left,
    "move_to_top_right":     _resolve_move_to_top_right,
    "move_to_bottom_left":   _resolve_move_to_bottom_left,
    "move_to_bottom_right":  _resolve_move_to_bottom_right,
    "move_to_top_center":    _resolve_move_to_top_center,
    "move_to_bottom_center": _resolve_move_to_bottom_center,
    "move_to_left_center":   _resolve_move_to_left_center,
    "move_to_right_center":  _resolve_move_to_right_center,
    "move_to_quarter_1":     _resolve_quarter(1),
    "move_to_quarter_2":     _resolve_quarter(2),
    "move_to_quarter_3":     _resolve_quarter(3),
    "move_to_quarter_4":     _resolve_quarter(4),
    "scroll_down":           _resolve_scroll_down,
    "scroll_up":             _resolve_scroll_up,
    "scroll_page_down":      _resolve_scroll_page_down,
    "scroll_page_up":        _resolve_scroll_page_up,
    "press_enter":           _resolve_press_enter,
    "press_tab":             _resolve_press_tab,
    "press_escape":          _resolve_press_escape,
    "press_space":           _resolve_press_space,
    "press_backspace":       _resolve_press_backspace,
    "press_delete":          _resolve_press_delete,
    "press_up":              _resolve_press_up,
    "press_down":            _resolve_press_down,
    "press_left":            _resolve_press_left,
    "press_right":           _resolve_press_right,
    "save_shortcut":         _resolve_save_shortcut,
    "copy_shortcut":         _resolve_copy_shortcut,
    "paste_shortcut":        _resolve_paste_shortcut,
    "undo_shortcut":         _resolve_undo_shortcut,
    "redo_shortcut":         _resolve_redo_shortcut,
    "select_all":            _resolve_select_all,
    "open_chrome":           _resolve_open_chrome,
    "open_firefox":          _resolve_open_firefox,
    "open_edge":             _resolve_open_edge,
    "open_brave":            _resolve_open_brave,
    "open_opera":            _resolve_open_opera,
    "open_notepad":          _resolve_open_notepad,
    "open_calculator":       _resolve_open_calculator,
    "open_vscode":           _resolve_open_vscode,
    "open_vs_code":          _resolve_open_vs_code,
    "open_paint":            _resolve_open_paint,
    "open_discord":          _resolve_open_discord,
    "open_spotify":          _resolve_open_spotify,
    "open_telegram":         _resolve_open_telegram,
    "open_slack":            _resolve_open_slack,
    "open_steam":            _resolve_open_steam,
    "open_word":             _resolve_open_word,
    "open_excel":            _resolve_open_excel,
    "open_powerpoint":       _resolve_open_powerpoint,
    "open_outlook":          _resolve_open_outlook,
    "open_explorer":         _resolve_open_explorer,
    "take_screenshot":       _resolve_take_screenshot,
    "capture_screen":        _resolve_take_screenshot,
}

# Hotkey shortcuts that need special positional-arg handling
_HOTKEY_SHORTCUTS: Dict[str, List[str]] = {
    "save_shortcut":  ["ctrl", "s"],
    "copy_shortcut":  ["ctrl", "c"],
    "paste_shortcut": ["ctrl", "v"],
    "undo_shortcut":  ["ctrl", "z"],
    "redo_shortcut":  ["ctrl", "y"],
    "select_all":     ["ctrl", "a"],
}


# ─────────────────────────────────────────────────────────────────────────────
# ActionTranslator
# ─────────────────────────────────────────────────────────────────────────────

class ActionTranslator:
    """
    Translates semantic action names into executable TranslatedActions.

    Usage
    -----
    translator = ActionTranslator()

    # Single translation
    result = translator.translate("move_to_center")
    action = result.to_control_action()

    # Batch translation
    actions = translator.translate_all([
        ("move_to_center", {}),
        ("search_google",  {"query": "latest AI"}),
        ("press_enter",    {}),
    ])
    """

    def __init__(self) -> None:
        self._map      = _SEMANTIC_MAP
        self._resolvers = _PARAM_RESOLVERS
        self._hotkeys  = _HOTKEY_SHORTCUTS

    # ── Public API ─────────────────────────────────────────────────────────────

    def translate(
        self,
        semantic_action: str,
        raw_params: Optional[dict] = None,
    ) -> Optional[TranslatedAction]:
        """
        Translate one semantic action name into a TranslatedAction.

        Returns None if the semantic action is unknown (logs a warning).
        Never raises — unknown actions are handled gracefully.
        """
        raw_params = raw_params or {}
        key        = semantic_action.lower().strip()

        # Look up in map
        entry = self._map.get(key)
        if entry is None:
            logger.warning(
                f"ActionTranslator: unknown semantic action {semantic_action!r} — skipped"
            )
            return None

        controller, method, risk = entry

        # Resolve parameters
        resolved_params = self._resolve_params(key, raw_params, method)

        # Build description
        description = self._describe(key, resolved_params)

        result = TranslatedAction(
            semantic_name = semantic_action,
            controller    = controller,
            method        = method,
            params        = resolved_params,
            risk          = risk,
            description   = description,
        )

        logger.info(
            f"ActionTranslator: {semantic_action!r} → "
            f"{controller.value}.{method}({resolved_params})"
        )
        return result

    def translate_all(
        self,
        semantic_actions: List[Tuple[str, dict]],
    ) -> List[ControlAction]:
        """
        Translate a list of (semantic_name, params) tuples.
        Unknown actions are skipped with a warning.
        Returns a list of ControlActions ready for ControlManager.
        """
        actions: List[ControlAction] = []
        for semantic, params in semantic_actions:
            result = self.translate(semantic, params)
            if result is not None:
                actions.append(result.to_control_action())
        return actions

    def is_known(self, semantic_action: str) -> bool:
        """Return True if the semantic action has a mapping."""
        return semantic_action.lower().strip() in self._map

    def list_actions(self) -> List[str]:
        """Return all known semantic action names."""
        return sorted(self._map.keys())

    def list_by_controller(self, controller: ControllerType) -> List[str]:
        """Return semantic actions that map to a specific controller."""
        return sorted(
            k for k, (c, _, _) in self._map.items() if c == controller
        )

    # ── Internal ───────────────────────────────────────────────────────────────

    def _resolve_params(
        self, key: str, raw: dict, method: str
    ) -> dict:
        """
        Apply the param resolver for this semantic action, then merge
        any remaining raw params that weren't overridden.
        """
        # Special case: hotkey shortcuts need positional keys
        if key in self._hotkeys:
            keys = self._hotkeys[key]
            # KeyboardController.hotkey(*keys) — pass as positional via special key
            return {"keys": keys}

        resolver = self._resolvers.get(key)
        if resolver:
            resolved = resolver(raw)
            # Merge: resolved takes priority, raw fills in anything not resolved
            merged = {**raw, **resolved}
            return merged

        # No resolver — pass raw params through unchanged
        return raw

    @staticmethod
    def _describe(key: str, params: dict) -> str:
        """Generate a human-readable description for the UI."""
        label = key.replace("_", " ").title()
        if "query" in params:
            return f"{label}: {params['query']!r}"
        if "text" in params:
            preview = str(params["text"])[:30]
            return f"{label}: {preview!r}"
        if "app_name" in params:
            return f"{label}: {params['app_name']}"
        if "x" in params and "y" in params:
            return f"{label} → ({params['x']}, {params['y']})"
        if "key" in params:
            return f"{label}: {params['key']}"
        if "keys" in params:
            return f"{label}: {'+'.join(params['keys'])}"
        if "url" in params:
            return f"{label}: {params['url']}"
        if "title" in params:
            return f"{label}: {params['title']!r}"
        return label


# Module-level singleton
action_translator = ActionTranslator()
