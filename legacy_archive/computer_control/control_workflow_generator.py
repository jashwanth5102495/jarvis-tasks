"""
control_workflow_generator.py
==============================
ControlWorkflowGenerator — Natural Language → Semantic Action List.

This is the top of the translation pipeline:

  User input (natural language)
       ↓
  ControlWorkflowGenerator.generate(text)
       ↓
  List of (semantic_action, params) tuples
       ↓
  ActionTranslator.translate_all(...)
       ↓
  List[ControlAction]
       ↓
  ControlManager.execute_actions(...)
       ↓
  Real desktop interaction

How it works
------------
1. Pattern matching against NL_PATTERNS — ordered list of
   (regex, semantic_action, param_extractor) tuples.
2. First match wins and returns the semantic action list.
3. If no pattern matches, falls back to keyword heuristics.
4. Unknown inputs return an empty list (safe — nothing executes).

Adding new patterns
-------------------
Append to NL_PATTERNS:
  (r"your regex here", "semantic_action_name", param_fn_or_None)

param_fn receives the re.Match object and returns a dict.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Type alias: (semantic_action_name, params_dict)
SemanticStep = Tuple[str, Dict[str, Any]]

# Type alias for a param extractor: Match → dict
ParamFn = Callable[[re.Match], Dict[str, Any]]


def _no_params(_m: re.Match) -> dict:
    return {}


def _query_from_group1(m: re.Match) -> dict:
    return {"query": m.group(1).strip()}


def _text_from_group1(m: re.Match) -> dict:
    return {"text": m.group(1).strip()}


def _app_from_group1(m: re.Match) -> dict:
    return {"app_name": m.group(1).strip().lower()}


def _url_from_group1(m: re.Match) -> dict:
    url = m.group(1).strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return {"url": url}


def _key_from_group1(m: re.Match) -> dict:
    return {"key": m.group(1).strip().lower()}


def _title_from_group1(m: re.Match) -> dict:
    return {"title": m.group(1).strip()}


def _clicks_from_group1(m: re.Match) -> dict:
    try:
        return {"clicks": int(m.group(1))}
    except (IndexError, ValueError):
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# NL_PATTERNS
# Each entry: (regex_pattern, semantic_action, param_fn)
# Patterns are checked in order — put more specific patterns first.
# ─────────────────────────────────────────────────────────────────────────────

NL_PATTERNS: List[Tuple[str, str, ParamFn]] = [

    # ── Mouse movement ─────────────────────────────────────────────────────────
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?center",   "move_to_center",        _no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?middle",   "move_to_center",        _no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?top\s+left",   "move_to_top_left",  _no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?top\s+right",  "move_to_top_right", _no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?bottom\s+left","move_to_bottom_left",_no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?bottom\s+right","move_to_bottom_right",_no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?top",      "move_to_top_center",    _no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?bottom",   "move_to_bottom_center", _no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?left",     "move_to_left_center",   _no_params),
    (r"move\s+(?:the\s+)?mouse\s+to\s+(?:the\s+)?right",    "move_to_right_center",  _no_params),
    (r"center\s+(?:the\s+)?mouse",                           "move_to_center",        _no_params),

    # ── Clicks ─────────────────────────────────────────────────────────────────
    (r"right[\s\-]?click",                                   "right_click",           _no_params),
    (r"double[\s\-]?click",                                  "double_click",          _no_params),
    (r"left[\s\-]?click",                                    "left_click",            _no_params),
    (r"\bclick\b",                                           "click",                 _no_params),

    # ── Scroll ─────────────────────────────────────────────────────────────────
    (r"scroll\s+(?:the\s+)?(?:page\s+)?down\s+(\d+)",       "scroll_down",           _clicks_from_group1),
    (r"scroll\s+(?:the\s+)?(?:page\s+)?up\s+(\d+)",         "scroll_up",             _clicks_from_group1),
    (r"scroll\s+(?:the\s+)?(?:page\s+)?down",               "scroll_down",           _no_params),
    (r"scroll\s+(?:the\s+)?(?:page\s+)?up",                 "scroll_up",             _no_params),
    (r"scroll\s+down",                                       "scroll_down",           _no_params),
    (r"scroll\s+up",                                         "scroll_up",             _no_params),

    # ── Keyboard — specific keys ───────────────────────────────────────────────
    (r"press\s+enter",                                       "press_enter",           _no_params),
    (r"hit\s+enter",                                         "press_enter",           _no_params),
    (r"press\s+tab",                                         "press_tab",             _no_params),
    (r"press\s+escape",                                      "press_escape",          _no_params),
    (r"press\s+esc",                                         "press_escape",          _no_params),
    (r"press\s+space",                                       "press_space",           _no_params),
    (r"press\s+backspace",                                   "press_backspace",       _no_params),
    (r"press\s+delete",                                      "press_delete",          _no_params),
    (r"press\s+up",                                          "press_up",              _no_params),
    (r"press\s+down",                                        "press_down",            _no_params),
    (r"press\s+left",                                        "press_left",            _no_params),
    (r"press\s+right",                                       "press_right",           _no_params),
    (r"press\s+(?:the\s+)?(\w+)\s+key",                     "press_key",             _key_from_group1),
    (r"press\s+(\w+)",                                       "press_key",             _key_from_group1),

    # ── Keyboard — shortcuts ───────────────────────────────────────────────────
    (r"save\s+(?:the\s+)?(?:file|document)",                 "save_shortcut",         _no_params),
    (r"ctrl\s*\+\s*s",                                       "save_shortcut",         _no_params),
    (r"copy\s+(?:that|it|text|selection)?",                  "copy_shortcut",         _no_params),
    (r"ctrl\s*\+\s*c",                                       "copy_shortcut",         _no_params),
    (r"paste\s+(?:that|it|text)?",                           "paste_shortcut",        _no_params),
    (r"ctrl\s*\+\s*v",                                       "paste_shortcut",        _no_params),
    (r"undo",                                                "undo_shortcut",         _no_params),
    (r"redo",                                                "redo_shortcut",         _no_params),
    (r"select\s+all",                                        "select_all",            _no_params),
    (r"clear\s+(?:the\s+)?(?:field|input|text)",             "clear_field",           _no_params),

    # ── Keyboard — type text ───────────────────────────────────────────────────
    (r'type\s+"([^"]+)"',                                    "type_text",             _text_from_group1),
    (r"type\s+'([^']+)'",                                    "type_text",             _text_from_group1),
    (r"type\s+(?:the\s+)?(?:text\s+)?(.+)",                 "type_text",             _text_from_group1),
    (r"write\s+(?:the\s+)?(?:text\s+)?(.+)",                "type_text",             _text_from_group1),

    # ── Browser — search ───────────────────────────────────────────────────────
    (r"search\s+(?:google\s+)?(?:for\s+)?(.+)",              "search_google",         _query_from_group1),
    (r"google\s+(.+)",                                       "search_google",         _query_from_group1),
    (r"bing\s+(?:search\s+)?(?:for\s+)?(.+)",               "search_bing",           _query_from_group1),
    (r"search\s+bing\s+(?:for\s+)?(.+)",                    "search_bing",           _query_from_group1),

    # ── Browser — navigation ───────────────────────────────────────────────────
    (r"open\s+(?:the\s+)?(?:url|website|site|page)\s+(.+)", "open_url",              _url_from_group1),
    (r"go\s+to\s+(.+)",                                      "open_url",              _url_from_group1),
    (r"navigate\s+to\s+(.+)",                                "navigate_to",           _url_from_group1),
    (r"new\s+tab",                                           "new_tab",               _no_params),
    (r"open\s+(?:a\s+)?new\s+tab",                          "new_tab",               _no_params),
    (r"close\s+(?:this\s+)?tab",                             "close_tab",             _no_params),
    (r"refresh\s+(?:the\s+)?(?:page|browser)",               "refresh_page",          _no_params),
    (r"go\s+back",                                           "go_back",               _no_params),
    (r"go\s+forward",                                        "go_forward",            _no_params),
    (r"focus\s+(?:the\s+)?browser",                          "focus_browser",         _no_params),

    # ── App launch ─────────────────────────────────────────────────────────────
    (r"open\s+(?:vs\s+code|vscode|visual\s+studio\s+code)",  "open_vscode",           _no_params),
    (r"launch\s+(?:vs\s+code|vscode|visual\s+studio\s+code)","open_vscode",           _no_params),
    (r"open\s+(?:google\s+)?chrome",                         "open_chrome",           _no_params),
    (r"launch\s+(?:google\s+)?chrome",                       "open_chrome",           _no_params),
    (r"open\s+brave(?:\s+browser)?",                         "open_brave",            _no_params),
    (r"launch\s+brave(?:\s+browser)?",                       "open_brave",            _no_params),
    (r"open\s+(?:mozilla\s+)?firefox",                       "open_firefox",          _no_params),
    (r"launch\s+(?:mozilla\s+)?firefox",                     "open_firefox",          _no_params),
    (r"open\s+(?:microsoft\s+)?edge",                        "open_edge",             _no_params),
    (r"launch\s+(?:microsoft\s+)?edge",                      "open_edge",             _no_params),
    (r"open\s+opera(?:\s+browser)?",                         "open_opera",            _no_params),
    (r"open\s+discord",                                      "open_discord",          _no_params),
    (r"launch\s+discord",                                    "open_discord",          _no_params),
    (r"open\s+spotify",                                      "open_spotify",          _no_params),
    (r"launch\s+spotify",                                    "open_spotify",          _no_params),
    (r"open\s+telegram",                                     "open_telegram",         _no_params),
    (r"launch\s+telegram",                                   "open_telegram",         _no_params),
    (r"open\s+slack",                                        "open_slack",            _no_params),
    (r"open\s+steam",                                        "open_steam",            _no_params),
    (r"launch\s+steam",                                      "open_steam",            _no_params),
    (r"open\s+notepad",                                      "open_notepad",          _no_params),
    (r"open\s+calculator",                                   "open_calculator",       _no_params),
    (r"open\s+paint",                                        "open_paint",            _no_params),
    (r"open\s+(?:microsoft\s+)?word",                        "open_word",             _no_params),
    (r"open\s+(?:microsoft\s+)?excel",                       "open_excel",            _no_params),
    (r"open\s+(?:microsoft\s+)?powerpoint",                  "open_powerpoint",       _no_params),
    (r"open\s+(?:microsoft\s+)?outlook",                     "open_outlook",          _no_params),
    (r"open\s+(?:file\s+)?explorer",                         "open_explorer",         _no_params),
    # Generic open-app fallback — matches "open X" for any X not caught above
    (r"open\s+(?:the\s+)?(?:app\s+)?(.+)",                  "open_app",              _app_from_group1),
    (r"launch\s+(?:the\s+)?(?:app\s+)?(.+)",                "launch_app",            _app_from_group1),

    # ── Window management ──────────────────────────────────────────────────────
    (r"maximize\s+(?:the\s+)?(?:window\s+)?(.+)",            "maximize_window",       _title_from_group1),
    (r"minimize\s+(?:the\s+)?(?:window\s+)?(.+)",            "minimize_window",       _title_from_group1),
    (r"focus\s+(?:the\s+)?(?:window\s+)?(.+)",               "focus_window",          _title_from_group1),
    (r"maximize\s+(?:the\s+)?window",                        "maximize_window",       lambda m: {"title": ""}),
    (r"minimize\s+(?:the\s+)?window",                        "minimize_window",       lambda m: {"title": ""}),
    (r"list\s+(?:all\s+)?(?:open\s+)?windows",               "list_windows",          _no_params),
    (r"what\s+(?:windows|apps)\s+are\s+open",                "list_windows",          _no_params),
    (r"active\s+window",                                     "get_active_window",     _no_params),
    (r"what\s+(?:is\s+)?(?:the\s+)?active\s+window",        "get_active_window",     _no_params),

    # ── Screenshot ─────────────────────────────────────────────────────────────
    (r"take\s+(?:a\s+)?screenshot",                          "take_screenshot",       _no_params),
    (r"capture\s+(?:the\s+)?screen",                         "capture_screen",        _no_params),
    (r"screenshot",                                          "take_screenshot",       _no_params),

    # ── Screen info ────────────────────────────────────────────────────────────
    (r"(?:get\s+)?screen\s+(?:size|info|resolution)",        "get_screen_info",       _no_params),
    (r"what\s+(?:is\s+)?(?:the\s+)?screen\s+(?:size|resolution)", "get_screen_info", _no_params),
]

# Pre-compile all patterns for performance
_COMPILED: List[Tuple[re.Pattern, str, ParamFn]] = [
    (re.compile(pat, re.IGNORECASE), action, fn)
    for pat, action, fn in NL_PATTERNS
]


# ─────────────────────────────────────────────────────────────────────────────
# ControlWorkflowGenerator
# ─────────────────────────────────────────────────────────────────────────────

class ControlWorkflowGenerator:
    """
    Converts natural language desktop control intents into semantic action lists.

    Usage
    -----
    gen = ControlWorkflowGenerator()
    steps = gen.generate("Move mouse to center")
    # → [("move_to_center", {})]

    steps = gen.generate("Search Google for latest AI models")
    # → [("search_google", {"query": "latest AI models"})]

    # Multi-step compound intent
    steps = gen.generate("Open Chrome and search for AI news")
    # → [("open_chrome", {}), ("search_google", {"query": "AI news"})]
    """

    def generate(self, text: str) -> List[SemanticStep]:
        """
        Parse natural language text and return a list of semantic steps.
        Returns [] if no pattern matches (safe — nothing will execute).
        """
        text_clean = text.strip()

        # Try compound intent splitting first ("X and Y")
        compound = self._try_compound(text_clean)
        if compound:
            logger.info(
                f"ControlWorkflowGenerator: compound intent → {[s for s,_ in compound]}"
            )
            return compound

        # Single intent match
        result = self._match_single(text_clean)
        if result:
            logger.info(
                f"ControlWorkflowGenerator: {text_clean!r} → {result[0][0]}"
            )
            return result

        logger.warning(
            f"ControlWorkflowGenerator: no pattern matched for {text_clean!r}"
        )
        return []

    def generate_from_input(
        self,
        user_input: str,
        category: str = "",
        requirements: list = None,
    ) -> List:
        """
        Entry point called from main.py for computer_control category goals.
        Returns a list of ControlAction objects (already translated).
        """
        from computer_control.action_translator import action_translator
        steps = self.generate(user_input)
        if not steps:
            return []
        return action_translator.translate_all(steps)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _match_single(self, text: str) -> List[SemanticStep]:
        """Try each pattern against the full text. Return first match."""
        for pattern, action, param_fn in _COMPILED:
            m = pattern.search(text)
            if m:
                params = param_fn(m)
                return [(action, params)]
        return []

    def _try_compound(self, text: str) -> List[SemanticStep]:
        """
        Split on ' and ' / ' then ' / ', then ' and try to match each part.
        Only returns results if ALL parts match.
        """
        # Split on common compound connectors
        parts = re.split(r"\s+(?:and\s+then|then|and|,\s*then)\s+", text, flags=re.IGNORECASE)
        if len(parts) < 2:
            return []

        steps: List[SemanticStep] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            matched = self._match_single(part)
            if not matched:
                # One part didn't match — fall back to single-intent matching
                return []
            steps.extend(matched)

        return steps if len(steps) >= 2 else []


# Module-level singleton
control_workflow_generator = ControlWorkflowGenerator()
