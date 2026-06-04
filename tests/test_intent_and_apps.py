"""
test_intent_and_apps.py
========================
Test suite for:
  - Short command intent classification
  - App alias registry resolution
  - Action translator app mappings
  - Workflow generator patterns
  - Requirements extractor noise filtering
  - Unicode logging (no crash)

All tests are SAFE — no actual mouse movement or app launching.
"""

from __future__ import annotations

import os
import sys
import logging
from unittest.mock import patch, MagicMock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rich.console import Console

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
# 1. Short Command Classification
# ─────────────────────────────────────────────────────────────────────────────

def test_short_command_classification():
    console.print("\n[bold cyan]── 1. Short Command Classification ────────────────────[/bold cyan]")
    from core.brain import Brain

    brain = Brain()

    cases = [
        ("Scroll down",    "computer_control"),
        ("Scroll up",      "computer_control"),
        ("Click",          "computer_control"),
        ("Right click",    "computer_control"),
        ("Double click",   "computer_control"),
        ("Press enter",    "computer_control"),
        ("Take screenshot","computer_control"),
        ("Open browser",   "computer_control"),
        ("Open Chrome",    "computer_control"),
        ("Open Brave",     "computer_control"),
        ("Open Firefox",   "computer_control"),
        ("Open Edge",      "computer_control"),
        ("Open Discord",   "computer_control"),
        ("Open Spotify",   "computer_control"),
        ("Open Steam",     "computer_control"),
        ("Open Telegram",  "computer_control"),
        ("Open Notepad",   "computer_control"),
        ("Open Calculator","computer_control"),
    ]

    for text, expected in cases:
        try:
            goal = brain.analyze_task(text)
            check(
                f'"{text}" -> {goal.category} ({goal.confidence:.0f}%)',
                goal.category == expected,
                f"expected {expected}, got {goal.category}",
            )
        except Exception as e:
            check(f'"{text}" -> no error', False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# 2. App Registry Resolution
# ─────────────────────────────────────────────────────────────────────────────

def test_app_alias_resolution():
    console.print("\n[bold cyan]── 2. App Registry Resolution ──────────────────────────[/bold cyan]")
    from computer_control.app_registry import AppRegistry, _REGISTRY_DATA

    reg = AppRegistry(_REGISTRY_DATA)

    # Exact alias matches
    cases = [
        ("chrome",          "chrome"),
        ("brave",           "brave"),
        ("firefox",         "firefox"),
        ("edge",            "edge"),
        ("opera",           "opera"),
        ("discord",         "discord"),
        ("spotify",         "spotify"),
        ("telegram",        "telegram"),
        ("slack",           "slack"),
        ("steam",           "steam"),
        ("notepad",         "notepad"),
        ("vscode",          "vscode"),
        ("calculator",      "calculator"),
        ("paint",           "paint"),
    ]

    for alias, expected_canonical in cases:
        c, e = reg.resolve(alias)
        check(f'resolve("{alias}") -> {c}', c == expected_canonical,
              f"expected {expected_canonical!r}, got {c!r}")

    # Alias variants (with "Open" prefix)
    prefix_cases = [
        ("Open Brave",           "brave"),
        ("Open Firefox",         "firefox"),
        ("Open Microsoft Edge",  "edge"),
        ("Open Google Chrome",   "chrome"),
        ("Launch Discord",       "discord"),
        ("Open Spotify",         "spotify"),
        ("Open Steam",           "steam"),
        ("Open Telegram",        "telegram"),
        ("Launch VS Code",       "vscode"),
        ("Open Visual Studio Code", "vscode"),
        ("Open Mozilla Firefox", "firefox"),
    ]

    for text, expected_canonical in prefix_cases:
        c, e = reg.resolve(text)
        check(f'resolve("{text}") -> {c}',
              c == expected_canonical,
              f"expected {expected_canonical!r}, got {c!r}")

    # Unknown app returns (None, None) — use a completely made-up name
    c, e = reg.resolve("xyzzy_totally_fake_app_42_notreal")
    check("unknown app returns (None, None)", c is None and e is None)

    # list_apps returns list
    apps = reg.list_apps()
    check("list_apps returns list",   isinstance(apps, list))
    check("list_apps has 25+ entries", len(apps) >= 25)
    check("'brave' in list_apps",     "brave"   in apps)
    check("'discord' in list_apps",   "discord" in apps)
    check("'spotify' in list_apps",   "spotify" in apps)

    # register runtime entry
    from computer_control.app_registry import AppEntry
    reg.register(AppEntry(
        canonical="mytestapp",
        executable="mytestapp.exe",
        aliases=["mytestapp", "my test app"],
    ))
    c2, _ = reg.resolve("my test app")
    check("runtime register + resolve works", c2 == "mytestapp")


# ─────────────────────────────────────────────────────────────────────────────
# 3. AppController — graceful unknown-app handling
# ─────────────────────────────────────────────────────────────────────────────

def test_app_controller_graceful():
    console.print("\n[bold cyan]── 3. AppController Graceful Handling ──────────────────[/bold cyan]")
    from computer_control.app_controller import AppController
    from computer_control.failsafe import failsafe
    failsafe.disable()

    ac = AppController()

    # Known app launches (mocked subprocess)
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        out = ac.open_app("brave")
        check("open_app('brave') succeeds",
              "brave" in out.lower() or "launched" in out.lower(), out)

        out2 = ac.open_app("discord")
        check("open_app('discord') succeeds",
              "discord" in out2.lower() or "launched" in out2.lower(), out2)

        out3 = ac.open_app("firefox")
        check("open_app('firefox') succeeds",
              "firefox" in out3.lower() or "launched" in out3.lower(), out3)

    # Unknown app returns friendly message — does NOT raise
    out_unknown = ac.open_app("nonexistent_app_xyz_999")
    check("unknown app returns message, no crash",
          "could not find" in out_unknown.lower() or "not in registry" in out_unknown.lower(),
          out_unknown)
    check("unknown app does not raise exception", True)  # reaching here means no raise

    # is_running (mocked)
    mock_proc = MagicMock()
    mock_proc.info = {"name": "brave.exe"}
    with patch("psutil.process_iter", return_value=[mock_proc]):
        out4 = ac.is_running("brave")
        check("is_running detects brave", "running" in out4.lower())

    # Unknown app is_running returns NOT running message
    with patch("psutil.process_iter", return_value=[]):
        out5 = ac.is_running("nonexistent_xyz")
        check("is_running unknown returns NOT running",
              "not" in out5.lower() or "not in registry" in out5.lower())


# ─────────────────────────────────────────────────────────────────────────────
# 4. Workflow Generator — new app patterns
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_generator_apps():
    console.print("\n[bold cyan]── 4. Workflow Generator — App Patterns ────────────────[/bold cyan]")
    from computer_control.control_workflow_generator import ControlWorkflowGenerator

    gen = ControlWorkflowGenerator()

    app_cases = [
        ("Open Brave",          "open_brave"),
        ("Open Firefox",        "open_firefox"),
        ("Open Edge",           "open_edge"),
        ("Open Microsoft Edge", "open_edge"),
        ("Open Discord",        "open_discord"),
        ("Open Spotify",        "open_spotify"),
        ("Open Telegram",       "open_telegram"),
        ("Open Steam",          "open_steam"),
        ("Launch Brave",        "open_brave"),
        ("Launch Discord",      "open_discord"),
        ("Open Calculator",     "open_calculator"),
        ("Open Paint",          "open_paint"),
        ("Open Word",           "open_word"),
        ("Open Excel",          "open_excel"),
        ("Open Notepad",        "open_notepad"),
    ]

    for text, expected_action in app_cases:
        steps = gen.generate(text)
        got = steps[0][0] if steps else "NO_MATCH"
        check(f'generate("{text}") -> {expected_action}',
              got == expected_action, f"got {got!r}")

    # Scroll commands
    scroll_cases = [
        ("Scroll down",          "scroll_down"),
        ("Scroll up",            "scroll_up"),
        ("Scroll the page down", "scroll_down"),
        ("Scroll down 5",        "scroll_down"),
    ]
    for text, expected_action in scroll_cases:
        steps = gen.generate(text)
        got = steps[0][0] if steps else "NO_MATCH"
        check(f'generate("{text}") -> {expected_action}',
              got == expected_action, f"got {got!r}")

    # Short commands
    short_cases = [
        ("Click",          "click"),
        ("Right click",    "right_click"),
        ("Double click",   "double_click"),
        ("Press enter",    "press_enter"),
        ("Take screenshot","take_screenshot"),
    ]
    for text, expected_action in short_cases:
        steps = gen.generate(text)
        got = steps[0][0] if steps else "NO_MATCH"
        check(f'generate("{text}") -> {expected_action}',
              got == expected_action, f"got {got!r}")

    # Generic open-app fallback
    steps_gen = gen.generate("Open Slack")
    check("generic open-app fallback works for Slack",
          len(steps_gen) > 0, "no steps generated")
    if steps_gen:
        check("generic fallback produces open_app action",
              "open" in steps_gen[0][0], f"got {steps_gen[0][0]!r}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Action Translator — new app mappings
# ─────────────────────────────────────────────────────────────────────────────

def test_action_translator_apps():
    console.print("\n[bold cyan]── 5. Action Translator — App Mappings ─────────────────[/bold cyan]")
    from computer_control.action_translator import ActionTranslator
    from computer_control.cc_models import ControllerType

    t = ActionTranslator()

    app_actions = [
        ("open_brave",      "brave"),
        ("open_firefox",    "firefox"),
        ("open_edge",       "edge"),
        ("open_discord",    "discord"),
        ("open_spotify",    "spotify"),
        ("open_telegram",   "telegram"),
        ("open_steam",      "steam"),
        ("open_word",       "word"),
        ("open_excel",      "excel"),
        ("open_powerpoint", "powerpoint"),
        ("open_outlook",    "outlook"),
        ("open_explorer",   "explorer"),
        ("open_opera",      "opera"),
    ]

    for semantic, expected_app_name in app_actions:
        r = t.translate(semantic)
        check(f'translate("{semantic}") not None', r is not None)
        if r:
            check(f'"{semantic}" -> app_name={expected_app_name!r}',
                  r.params.get("app_name") == expected_app_name,
                  f"got {r.params.get('app_name')!r}")
            check(f'"{semantic}" uses APP controller',
                  r.controller == ControllerType.APP)

    # Scroll actions have correct click directions
    r_down = t.translate("scroll_down")
    check("scroll_down clicks < 0", r_down.params.get("clicks", 0) < 0)

    r_up = t.translate("scroll_up")
    check("scroll_up clicks > 0", r_up.params.get("clicks", 0) > 0)

    # is_known for all new apps
    new_apps = ["open_brave", "open_discord", "open_spotify", "open_telegram",
                "open_steam", "open_word", "open_excel"]
    for sem in new_apps:
        check(f'is_known("{sem}")', t.is_known(sem))


# ─────────────────────────────────────────────────────────────────────────────
# 6. Requirements Extractor — no noise words
# ─────────────────────────────────────────────────────────────────────────────

def test_extractor_no_noise():
    console.print("\n[bold cyan]── 6. Requirements Extractor — No Noise Words ──────────[/bold cyan]")
    from brain.extractor import RequirementsExtractor

    ex = RequirementsExtractor()

    # Desktop commands should NOT extract UI noise words
    noise_cases = [
        ("Scroll down",     ["enter", "scroll", "screen", "click", "text", "mouse"]),
        ("Press enter",     ["enter", "press", "tab"]),
        ("Take screenshot", ["screen", "capture", "take"]),
        ("Click",           ["click"]),
        ("Right click",     ["click", "right"]),
    ]

    for text, forbidden_words in noise_cases:
        reqs = ex.extract(text, text.lower().split())
        for forbidden in forbidden_words:
            check(f'"{text}" does not extract noise word "{forbidden}"',
                  forbidden not in [r.lower() for r in reqs],
                  f"requirements={reqs}")

    # App name SHOULD be extracted
    app_cases = [
        ("Open Brave",    "brave"),
        ("Open Discord",  "discord"),
        ("Open Firefox",  "firefox"),
        ("Open Spotify",  "spotify"),
        ("Open Chrome",   "chrome"),
    ]
    for text, expected_req in app_cases:
        reqs = ex.extract(text, text.lower().split())
        reqs_lower = [r.lower() for r in reqs]
        check(f'"{text}" extracts app name "{expected_req}"',
              expected_req in reqs_lower or
              any(expected_req in r for r in reqs_lower),
              f"requirements={reqs}")

    # Software task requirements still work
    reqs_flask = ex.extract(
        "Build Flask API project", ["flask", "api", "project"]
    )
    check("Flask task extracts 'api'",
          any("api" in r.lower() for r in reqs_flask),
          f"requirements={reqs_flask}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Unicode Logging — no crash
# ─────────────────────────────────────────────────────────────────────────────

def test_unicode_logging():
    console.print("\n[bold cyan]── 7. Unicode Logging — No Crash ───────────────────────[/bold cyan]")

    logger = logging.getLogger("test_unicode")

    # These should NOT raise UnicodeEncodeError on Windows cp1252
    try:
        logger.info("Action Translator: open_chrome -> app.open_app")
        logger.info("Goal generated: Category=computer_control, Confidence=95.0%")
        logger.info("AppController: launched brave (brave.exe)")
        logger.info("Workflow: scroll_down -> mouse.scroll(clicks=-3)")
        logger.warning("Permission denied: action denied by policy")
        check("Unicode-free logging does not crash", True)
    except UnicodeEncodeError as e:
        check("Unicode-free logging does not crash", False, str(e))

    # Verify log file uses utf-8 encoding
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(
        suffix=".log", delete=False, mode="w", encoding="utf-8"
    )
    tmp_name = tmp.name
    tmp.close()   # close the NamedTemporaryFile handle before the handler opens it
    try:
        utf8_handler = logging.FileHandler(tmp_name, encoding="utf-8")
        test_logger  = logging.getLogger("test_utf8_log")
        test_logger.addHandler(utf8_handler)
        test_logger.setLevel(logging.DEBUG)
        test_logger.info("Test arrow ASCII: ->")
        test_logger.info("App: brave, discord, spotify")
        utf8_handler.close()
        test_logger.removeHandler(utf8_handler)
        check("UTF-8 log file written successfully", os.path.exists(tmp_name))
        content = open(tmp_name, encoding="utf-8").read()
        check("UTF-8 log file is readable", "brave" in content)
    finally:
        try:
            os.unlink(tmp_name)
        except PermissionError:
            pass   # Windows: file handle may still be held briefly


# ─────────────────────────────────────────────────────────────────────────────
# 8. Validator — gibberish fix
# ─────────────────────────────────────────────────────────────────────────────

def test_validator_gibberish_fix():
    console.print("\n[bold cyan]── 8. Validator — Gibberish Pattern Fix ────────────────[/bold cyan]")
    from brain.validator import InputValidator

    v = InputValidator()

    # These MUST pass (real words, even if letters happen to be on keyboard rows)
    valid_words = [
        ("Click",    ["click"]),
        ("Scroll",   ["scroll"]),
        ("Brave",    ["brave"]),
        ("Discord",  ["discord"]),
        ("Firefox",  ["firefox"]),
        ("Press",    ["press"]),
        ("Screen",   ["screen"]),
    ]
    for text, tokens in valid_words:
        ok, msg = v.validate(text, tokens)
        check(f'"{text}" passes validation', ok, msg)

    # These MUST fail (actual gibberish)
    invalid = [
        ("qwerty",     ["qwerty"]),
        ("asdfgh",     ["asdfgh"]),
        ("1234567",    ["1234567"]),
        ("zzzzzz",     ["zzzzzz"]),
    ]
    for text, tokens in invalid:
        ok, msg = v.validate(text, tokens)
        check(f'"{text}" correctly rejected', not ok, f"was accepted")


# ─────────────────────────────────────────────────────────────────────────────
# 9. Full NL → ControlAction pipeline (mocked execution)
# ─────────────────────────────────────────────────────────────────────────────

def test_full_nl_pipeline():
    console.print("\n[bold cyan]── 9. Full NL -> ControlAction Pipeline ────────────────[/bold cyan]")
    from computer_control.control_workflow_generator import control_workflow_generator
    from computer_control.cc_models import ControllerType

    with patch("pyautogui.size", return_value=(1920, 1080)):
        pipeline_cases = [
            ("Scroll down",   ControllerType.MOUSE,    "scroll"),
            ("Scroll up",     ControllerType.MOUSE,    "scroll"),
            ("Right click",   ControllerType.MOUSE,    "right_click"),
            ("Press enter",   ControllerType.KEYBOARD, "press"),
            ("Open Brave",    ControllerType.APP,      "open_app"),
            ("Open Discord",  ControllerType.APP,      "open_app"),
            ("Open Firefox",  ControllerType.APP,      "open_app"),
            ("Open Spotify",  ControllerType.APP,      "open_app"),
            ("Take screenshot", ControllerType.SCREENSHOT, "capture_screen"),
        ]

        for text, expected_ctrl, expected_action in pipeline_cases:
            actions = control_workflow_generator.generate_from_input(text)
            check(f'NL pipeline "{text}" generates actions', len(actions) > 0,
                  "no actions generated")
            if actions:
                a = actions[0]
                check(f'"{text}" -> controller={expected_ctrl.value}',
                      a.controller == expected_ctrl,
                      f"got {a.controller.value}")
                check(f'"{text}" -> action={expected_action!r}',
                      a.action == expected_action,
                      f"got {a.action!r}")

        # App params resolved correctly
        brave_actions = control_workflow_generator.generate_from_input("Open Brave")
        if brave_actions:
            check("Open Brave -> app_name='brave'",
                  brave_actions[0].params.get("app_name") == "brave",
                  str(brave_actions[0].params))

        discord_actions = control_workflow_generator.generate_from_input("Open Discord")
        if discord_actions:
            check("Open Discord -> app_name='discord'",
                  discord_actions[0].params.get("app_name") == "discord",
                  str(discord_actions[0].params))

        # Unknown input returns empty list
        unknown = control_workflow_generator.generate_from_input("xyzzy frobnicator blorp")
        check("unknown NL input returns empty list", unknown == [])


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_short_command_classification()
    test_app_alias_resolution()
    test_app_controller_graceful()
    test_workflow_generator_apps()
    test_action_translator_apps()
    test_extractor_no_noise()
    test_unicode_logging()
    test_validator_gibberish_fix()
    test_full_nl_pipeline()

    total = _results["pass"] + _results["fail"]
    console.print(f"\n{'=' * 60}")
    console.print(
        f"  Results: [green]{_results['pass']}[/green]/{total} passed  "
        f"([red]{_results['fail']}[/red] failed)"
    )
    console.print(f"{'=' * 60}\n")

    sys.exit(0 if _results["fail"] == 0 else 1)
