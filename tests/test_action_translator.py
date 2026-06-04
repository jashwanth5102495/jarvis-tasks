"""
test_action_translator.py
=========================
Automated test suite for the Semantic → Executable translation layer.

Covers
------
1.  CoordinateUtils — screen helpers
2.  ActionTranslator — mapping, param resolution, unknown handling
3.  ControlWorkflowGenerator — NL pattern matching, compound intents
4.  Full pipeline: NL → TranslatedAction → ControlAction
5.  ControlManager.execute_semantic (mocked controllers)
6.  Real safe actions (mouse position read, screen info)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rich.console import Console

from computer_control.cc_models import ActionRisk, ActionStatus, ControllerType
from computer_control.failsafe import failsafe

failsafe.disable()   # safe for headless testing

console = Console()
_results = {"pass": 0, "fail": 0}


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        _results["pass"] += 1
        console.print(f"  [green]✓[/green]  {label}")
    else:
        _results["fail"] += 1
        suffix = f"  [dim]({detail})[/dim]" if detail else ""
        console.print(f"  [red]✗[/red]  {label}{suffix}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. CoordinateUtils
# ─────────────────────────────────────────────────────────────────────────────

def test_coordinate_utils():
    console.print("\n[bold cyan]── 1. CoordinateUtils ──────────────────────────────────[/bold cyan]")
    from computer_control.coordinate_utils import (
        get_screen_center, get_screen_size, get_top_left, get_top_right,
        get_bottom_left, get_bottom_right, get_top_center, get_bottom_center,
        get_left_center, get_right_center, get_quarter, offset_from_center, clamp,
    )

    with patch("pyautogui.size", return_value=(1920, 1080)):
        w, h = get_screen_size()
        check("get_screen_size returns (1920, 1080)", (w, h) == (1920, 1080))

        cx, cy = get_screen_center()
        check("get_screen_center returns (960, 540)", (cx, cy) == (960, 540))

        tl = get_top_left()
        check("get_top_left returns (2, 2)", tl == (2, 2))

        tr = get_top_right()
        check("get_top_right x near screen width", tr[0] >= 1918)

        bl = get_bottom_left()
        check("get_bottom_left y near screen height", bl[1] >= 1078)

        br = get_bottom_right()
        check("get_bottom_right is near (1918, 1078)", br[0] >= 1918 and br[1] >= 1078)

        tc = get_top_center()
        check("get_top_center x == 960", tc[0] == 960)

        bc = get_bottom_center()
        check("get_bottom_center x == 960", bc[0] == 960)

        lc = get_left_center()
        check("get_left_center y == 540", lc[1] == 540)

        rc = get_right_center()
        check("get_right_center y == 540", rc[1] == 540)

        q1 = get_quarter(1)
        check("quarter 1 is top-left quadrant", q1[0] < 960 and q1[1] < 540)

        q4 = get_quarter(4)
        check("quarter 4 is bottom-right quadrant", q4[0] > 960 and q4[1] > 540)

        off = offset_from_center(100, -50)
        check("offset_from_center(100,-50) = (1060, 490)", off == (1060, 490))

        clamped = clamp(9999, 9999)
        check("clamp(9999,9999) stays within screen", clamped[0] <= 1918 and clamped[1] <= 1078)

        clamped2 = clamp(-100, -100)
        check("clamp(-100,-100) floors at margin", clamped2[0] >= 2 and clamped2[1] >= 2)


# ─────────────────────────────────────────────────────────────────────────────
# 2. ActionTranslator — mapping
# ─────────────────────────────────────────────────────────────────────────────

def test_action_translator_mapping():
    console.print("\n[bold cyan]── 2. ActionTranslator — Mapping ───────────────────────[/bold cyan]")
    from computer_control.action_translator import ActionTranslator

    t = ActionTranslator()

    # Known actions return TranslatedAction
    with patch("pyautogui.size", return_value=(1920, 1080)):
        result = t.translate("move_to_center")
        check("move_to_center translates", result is not None)
        check("move_to_center → mouse controller",
              result.controller == ControllerType.MOUSE)
        check("move_to_center → move_to method", result.method == "move_to")
        check("move_to_center injects x=960", result.params.get("x") == 960)
        check("move_to_center injects y=540", result.params.get("y") == 540)
        check("move_to_center risk is MEDIUM", result.risk == ActionRisk.MEDIUM)

    # right_click
    r2 = t.translate("right_click")
    check("right_click → mouse.right_click", r2.method == "right_click")
    check("right_click risk is HIGH", r2.risk == ActionRisk.HIGH)

    # double_click
    r3 = t.translate("double_click")
    check("double_click → mouse.double_click", r3.method == "double_click")

    # scroll_down injects negative clicks
    r4 = t.translate("scroll_down")
    check("scroll_down → mouse.scroll", r4.method == "scroll")
    check("scroll_down clicks is negative", r4.params.get("clicks", 0) < 0)

    # scroll_up injects positive clicks
    r5 = t.translate("scroll_up")
    check("scroll_up clicks is positive", r5.params.get("clicks", 0) > 0)

    # press_enter
    r6 = t.translate("press_enter")
    check("press_enter → keyboard.press", r6.method == "press")
    check("press_enter key == 'enter'", r6.params.get("key") == "enter")

    # press_tab
    r7 = t.translate("press_tab")
    check("press_tab key == 'tab'", r7.params.get("key") == "tab")

    # save_shortcut
    r8 = t.translate("save_shortcut")
    check("save_shortcut → keyboard.hotkey", r8.method == "hotkey")
    check("save_shortcut keys == ['ctrl','s']",
          r8.params.get("keys") == ["ctrl", "s"])

    # copy_shortcut
    r9 = t.translate("copy_shortcut")
    check("copy_shortcut keys == ['ctrl','c']",
          r9.params.get("keys") == ["ctrl", "c"])

    # search_google with query
    r10 = t.translate("search_google", {"query": "AI models"})
    check("search_google → browser.search_google", r10.method == "search_google")
    check("search_google query preserved", r10.params.get("query") == "AI models")

    # open_chrome
    r11 = t.translate("open_chrome")
    check("open_chrome → app.open_app", r11.method == "open_app")
    check("open_chrome app_name == 'chrome'", r11.params.get("app_name") == "chrome")

    # open_notepad
    r12 = t.translate("open_notepad")
    check("open_notepad app_name == 'notepad'", r12.params.get("app_name") == "notepad")

    # take_screenshot
    r13 = t.translate("take_screenshot")
    check("take_screenshot → screenshot.capture_screen",
          r13.controller == ControllerType.SCREENSHOT)

    # get_screen_info
    r14 = t.translate("get_screen_info")
    check("get_screen_info → screen controller",
          r14.controller == ControllerType.SCREEN)

    # Unknown action returns None (no crash)
    r_unknown = t.translate("move_mouse_diagonally_in_a_spiral")
    check("unknown action returns None", r_unknown is None)

    # is_known
    check("is_known('move_to_center') True",  t.is_known("move_to_center"))
    check("is_known('nonexistent') False",    not t.is_known("nonexistent"))

    # list_actions
    actions = t.list_actions()
    check("list_actions returns list",        isinstance(actions, list))
    check("list_actions contains move_to_center", "move_to_center" in actions)
    check("list_actions contains search_google",  "search_google"  in actions)

    # list_by_controller
    mouse_actions = t.list_by_controller(ControllerType.MOUSE)
    check("list_by_controller(MOUSE) contains move_to_center",
          "move_to_center" in mouse_actions)
    check("list_by_controller(MOUSE) contains scroll_down",
          "scroll_down" in mouse_actions)


# ─────────────────────────────────────────────────────────────────────────────
# 3. ActionTranslator — to_control_action
# ─────────────────────────────────────────────────────────────────────────────

def test_translated_action_to_control_action():
    console.print("\n[bold cyan]── 3. TranslatedAction → ControlAction ─────────────────[/bold cyan]")
    from computer_control.action_translator import ActionTranslator

    t = ActionTranslator()

    with patch("pyautogui.size", return_value=(1920, 1080)):
        ta = t.translate("move_to_center")
        ca = ta.to_control_action()

        check("to_control_action returns ControlAction",
              ca.__class__.__name__ == "ControlAction")
        check("ControlAction controller == MOUSE",
              ca.controller == ControllerType.MOUSE)
        check("ControlAction action == 'move_to'", ca.action == "move_to")
        check("ControlAction params has x", "x" in ca.params)
        check("ControlAction params has y", "y" in ca.params)
        check("ControlAction risk == MEDIUM", ca.risk == ActionRisk.MEDIUM)
        check("ControlAction description set", bool(ca.description))

    # translate_all
    with patch("pyautogui.size", return_value=(1920, 1080)):
        actions = t.translate_all([
            ("move_to_center", {}),
            ("press_enter",    {}),
            ("take_screenshot",{}),
            ("nonexistent_xyz",{}),   # should be skipped
        ])
        check("translate_all returns 3 actions (skips unknown)", len(actions) == 3)
        check("first action is move_to", actions[0].action == "move_to")
        check("second action is press",  actions[1].action == "press")
        check("third action is capture_screen", actions[2].action == "capture_screen")


# ─────────────────────────────────────────────────────────────────────────────
# 4. ControlWorkflowGenerator — NL pattern matching
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_generator_patterns():
    console.print("\n[bold cyan]── 4. ControlWorkflowGenerator — NL Patterns ───────────[/bold cyan]")
    from computer_control.control_workflow_generator import ControlWorkflowGenerator

    gen = ControlWorkflowGenerator()

    cases = [
        # (input_text, expected_semantic_action, check_label)
        ("Move mouse to center",              "move_to_center",    "move mouse to center"),
        ("Move the mouse to the middle",      "move_to_center",    "move mouse to middle"),
        ("Move mouse to top left",            "move_to_top_left",  "move to top left"),
        ("Move mouse to bottom right",        "move_to_bottom_right","move to bottom right"),
        ("Right click",                       "right_click",       "right click"),
        ("Double click",                      "double_click",      "double click"),
        ("Left click",                        "left_click",        "left click"),
        ("Click",                             "click",             "click"),
        ("Scroll down",                       "scroll_down",       "scroll down"),
        ("Scroll up",                         "scroll_up",         "scroll up"),
        ("Press enter",                       "press_enter",       "press enter"),
        ("Hit enter",                         "press_enter",       "hit enter"),
        ("Press tab",                         "press_tab",         "press tab"),
        ("Press escape",                      "press_escape",      "press escape"),
        ("Press space",                       "press_space",       "press space"),
        ("Save the file",                     "save_shortcut",     "save file"),
        ("Copy that",                         "copy_shortcut",     "copy"),
        ("Paste it",                          "paste_shortcut",    "paste"),
        ("Undo",                              "undo_shortcut",     "undo"),
        ("Select all",                        "select_all",        "select all"),
        ('Type "Hello World"',                "type_text",         "type quoted text"),
        ("Search for latest AI models",       "search_google",     "search google"),
        ("Google latest AI models",           "search_google",     "google search"),
        ("Open Chrome",                       "open_chrome",       "open chrome"),
        ("Launch Chrome",                     "open_chrome",       "launch chrome"),
        ("Open Notepad",                      "open_notepad",      "open notepad"),
        ("Open VS Code",                      "open_vscode",       "open vscode"),
        ("Open Visual Studio Code",           "open_vscode",       "open visual studio code"),
        ("New tab",                           "new_tab",           "new tab"),
        ("Close this tab",                    "close_tab",         "close tab"),
        ("Refresh the page",                  "refresh_page",      "refresh page"),
        ("Go back",                           "go_back",           "go back"),
        ("Go forward",                        "go_forward",        "go forward"),
        ("Take a screenshot",                 "take_screenshot",   "take screenshot"),
        ("Capture the screen",                "capture_screen",    "capture screen"),
        ("Get screen info",                   "get_screen_info",   "screen info"),
        ("List all open windows",             "list_windows",      "list windows"),
        ("Active window",                     "get_active_window", "active window"),
    ]

    for text, expected_action, label in cases:
        steps = gen.generate(text)
        got = steps[0][0] if steps else "NO_MATCH"
        check(f'"{label}" → {expected_action}',
              got == expected_action,
              f"got {got!r}")


def test_workflow_generator_params():
    console.print("\n[bold cyan]── 5. ControlWorkflowGenerator — Param Extraction ──────[/bold cyan]")
    from computer_control.control_workflow_generator import ControlWorkflowGenerator

    gen = ControlWorkflowGenerator()

    # Search query extraction
    steps = gen.generate("Search for latest AI models")
    check("search query extracted",
          steps[0][1].get("query") == "latest AI models",
          f"got {steps[0][1]}")

    # Type text extraction
    steps2 = gen.generate('Type "Hello JARVIS"')
    check("type text extracted",
          steps2[0][1].get("text") == "Hello JARVIS",
          f"got {steps2[0][1]}")

    # App name extraction
    steps3 = gen.generate("Open Chrome")
    check("open chrome app_name == 'chrome'",
          steps3[0][1].get("app_name") == "chrome")

    # URL extraction
    steps4 = gen.generate("Go to https://google.com")
    check("URL extracted",
          "google.com" in steps4[0][1].get("url", ""))

    # Unknown input returns empty list
    steps5 = gen.generate("xyzzy frobnicator blorp")
    check("unknown input returns empty list", steps5 == [])


def test_workflow_generator_compound():
    console.print("\n[bold cyan]── 6. ControlWorkflowGenerator — Compound Intents ──────[/bold cyan]")
    from computer_control.control_workflow_generator import ControlWorkflowGenerator

    gen = ControlWorkflowGenerator()

    # "X and Y"
    steps = gen.generate("Open Chrome and search for AI news")
    check("compound: 2 steps generated", len(steps) == 2,
          f"got {len(steps)}")
    check("compound step 1 is open_chrome", steps[0][0] == "open_chrome")
    check("compound step 2 is search_google", steps[1][0] == "search_google")
    check("compound search query extracted",
          "AI news" in steps[1][1].get("query", ""))

    # "X then Y"
    steps2 = gen.generate("Press enter then take a screenshot")
    check("'then' compound: 2 steps", len(steps2) == 2)
    check("step 1 is press_enter",    steps2[0][0] == "press_enter")
    check("step 2 is take_screenshot",steps2[1][0] == "take_screenshot")

    # "X and then Y"
    steps3 = gen.generate("Scroll down and then scroll up")
    check("'and then' compound: 2 steps", len(steps3) == 2)
    check("step 1 is scroll_down", steps3[0][0] == "scroll_down")
    check("step 2 is scroll_up",   steps3[1][0] == "scroll_up")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Full pipeline: NL → ControlAction (mocked execution)
# ─────────────────────────────────────────────────────────────────────────────

def test_full_pipeline_mocked():
    console.print("\n[bold cyan]── 7. Full Pipeline: NL → ControlAction (mocked) ───────[/bold cyan]")
    from computer_control.control_manager import ControlManager
    from computer_control.cc_permissions import CCPermissionManager, CCPermissionMode

    pm = CCPermissionManager()
    for ctrl in ("mouse", "keyboard", "browser", "app", "screen", "screenshot"):
        for act in ("move_to", "click", "right_click", "double_click", "scroll",
                    "press", "hotkey", "type_text", "search_google", "open_app",
                    "capture_screen", "get_screen_info"):
            pm.set_override(ctrl, act, CCPermissionMode.ALLOW)

    cm = ControlManager(permission_manager=pm)
    mock_ctrl = MagicMock()
    mock_ctrl.execute.return_value = "mock ok"
    for key in list(cm._controllers.keys()):
        cm._controllers[key] = mock_ctrl

    with patch("pyautogui.size", return_value=(1920, 1080)):
        # move_to_center
        result = cm.execute_semantic_one("move_to_center", goal="move mouse to center")
        check("move_to_center executes", result.success_count == 1)
        check("move_to_center no failures", result.failed_count == 0)

        # right_click
        result2 = cm.execute_semantic_one("right_click", goal="right click")
        check("right_click executes", result2.success_count == 1)

        # scroll_down
        result3 = cm.execute_semantic_one("scroll_down", goal="scroll down")
        check("scroll_down executes", result3.success_count == 1)

        # press_enter
        result4 = cm.execute_semantic_one("press_enter", goal="press enter")
        check("press_enter executes", result4.success_count == 1)

        # search_google
        result5 = cm.execute_semantic_one(
            "search_google", {"query": "latest AI models"}, goal="search google"
        )
        check("search_google executes", result5.success_count == 1)

        # open_chrome
        result6 = cm.execute_semantic_one("open_chrome", goal="open chrome")
        check("open_chrome executes", result6.success_count == 1)

        # take_screenshot
        result7 = cm.execute_semantic_one("take_screenshot", goal="screenshot")
        check("take_screenshot executes", result7.success_count == 1)

        # execute_semantic batch
        result8 = cm.execute_semantic([
            ("move_to_center", {}),
            ("take_screenshot", {}),
            ("press_enter", {}),
        ], goal="batch test")
        check("batch: 3 actions succeed", result8.success_count == 3)

        # Unknown semantic action → empty result (no crash)
        result9 = cm.execute_semantic(
            [("totally_unknown_action_xyz", {})], goal="unknown"
        )
        check("unknown semantic action: no crash", result9 is not None)
        check("unknown semantic action: 0 successes", result9.success_count == 0)


# ─────────────────────────────────────────────────────────────────────────────
# 8. generate_from_input (main.py integration point)
# ─────────────────────────────────────────────────────────────────────────────

def test_generate_from_input():
    console.print("\n[bold cyan]── 8. generate_from_input (main.py integration) ────────[/bold cyan]")
    from computer_control.control_workflow_generator import control_workflow_generator

    with patch("pyautogui.size", return_value=(1920, 1080)):
        actions = control_workflow_generator.generate_from_input(
            "Move mouse to center", "computer_control", []
        )
        check("generate_from_input returns list", isinstance(actions, list))
        check("generate_from_input returns 1 action", len(actions) == 1)
        check("action is ControlAction",
              actions[0].__class__.__name__ == "ControlAction")
        check("action controller is mouse",
              actions[0].controller == ControllerType.MOUSE)
        check("action method is move_to", actions[0].action == "move_to")

        # Multi-step
        actions2 = control_workflow_generator.generate_from_input(
            "Open Chrome and search for AI news", "computer_control", []
        )
        check("compound generate_from_input returns 2 actions", len(actions2) == 2)

        # Unknown input returns empty list
        actions3 = control_workflow_generator.generate_from_input(
            "xyzzy frobnicator", "computer_control", []
        )
        check("unknown input returns empty list", actions3 == [])


# ─────────────────────────────────────────────────────────────────────────────
# 9. Real safe actions (no mocking — actual pyautogui calls)
# ─────────────────────────────────────────────────────────────────────────────

def test_real_safe_actions():
    console.print("\n[bold cyan]── 9. Real Safe Actions ────────────────────────────────[/bold cyan]")
    from computer_control.mouse_controller import MouseController
    from computer_control.screen_analyzer import ScreenAnalyzer

    mc = MouseController()
    sa = ScreenAnalyzer()

    # get_position — reads current mouse position, no movement
    pos = mc.get_position()
    check("get_position returns string", isinstance(pos, str))
    check("get_position contains coordinates", "position" in pos.lower() or "(" in pos)

    # screen_size — reads display info
    w, h = mc.screen_size()
    check("screen_size returns positive width",  w > 0)
    check("screen_size returns positive height", h > 0)

    # get_screen_info
    info = sa.get_screen_info()
    check("get_screen_info returns string", isinstance(info, str))
    check("get_screen_info contains resolution", "×" in info or "x" in info.lower())


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_coordinate_utils()
    test_action_translator_mapping()
    test_translated_action_to_control_action()
    test_workflow_generator_patterns()
    test_workflow_generator_params()
    test_workflow_generator_compound()
    test_full_pipeline_mocked()
    test_generate_from_input()
    test_real_safe_actions()

    total = _results["pass"] + _results["fail"]
    console.print(f"\n{'═' * 60}")
    console.print(
        f"  Results: [green]{_results['pass']}[/green]/{total} passed  "
        f"([red]{_results['fail']}[/red] failed)"
    )
    console.print(f"{'═' * 60}\n")

    sys.exit(0 if _results["fail"] == 0 else 1)
