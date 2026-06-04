"""
test_computer_control.py
========================
Automated test suite for JARVIS Milestone 4 — Computer Control System.

ALL tests are SAFE — no actual mouse movement, keyboard input, or
application launching occurs. Every controller is tested in isolation
using mocked PyAutoGUI calls so the suite runs headlessly in CI.

Covers
------
1.  FailSafe system — stop flag, reset, bounds clamping
2.  CCPermissionManager — auto-approve, confirm, deny, session allow
3.  ControlAction models — lifecycle, serialisation
4.  ActionQueue — enqueue, run, retry, emergency stop
5.  MouseController — action dispatch, bounds checking, blocked actions
6.  KeyboardController — type_text, hotkey blocking, length limit
7.  ScreenshotManager — capture, save, list (mocked)
8.  WindowManager — list, focus, active window (mocked)
9.  AppController — whitelist, open, is_running (mocked)
10. BrowserController — open_url, search, tab control (mocked)
11. UILocator — locate, wait, image_exists (mocked)
12. ScreenAnalyzer — screen info, pixel color, analyze screenshot
13. ControlManager — dispatch, workflow execution, logging
14. Full workflow: open_chrome_and_search (mocked)
15. Full workflow: screenshot_workflow (mocked)
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rich.console import Console

from computer_control.cc_models import (
    ActionRisk, ActionStatus, ControlAction, ControlResult, ControllerType
)
from computer_control.cc_permissions import CCPermissionManager, CCPermissionMode
from computer_control.failsafe import FailSafeSystem, FailSafeTriggered
from computer_control.action_queue import ActionQueue

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


def _action(
    controller: ControllerType = ControllerType.MOUSE,
    action: str = "move_to",
    params: dict = None,
    risk: ActionRisk = ActionRisk.MEDIUM,
    desc: str = "test action",
) -> ControlAction:
    return ControlAction(
        controller=controller, action=action,
        params=params or {"x": 100, "y": 100},
        risk=risk, description=desc,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. FailSafe System
# ─────────────────────────────────────────────────────────────────────────────

def test_failsafe():
    console.print("\n[bold cyan]── 1. FailSafe System ──────────────────────────────────[/bold cyan]")
    fs = FailSafeSystem()
    fs.disable()   # disable for testing so pyautogui isn't needed

    check("starts not stopped", not fs.is_stopped())

    fs.trigger_stop()
    check("trigger_stop sets flag", fs.is_stopped())

    try:
        fs.enable()
        fs.check()
        check("check() raises when stopped", False)
    except FailSafeTriggered:
        check("check() raises when stopped", True)

    fs.reset()
    check("reset clears stop flag", not fs.is_stopped())

    # check() passes after reset
    fs.disable()
    fs.check()   # should not raise
    check("check() passes after reset+disable", True)

    # Bounds clamping (mocked screen size)
    with patch("pyautogui.size", return_value=(1920, 1080)):
        x, y = FailSafeSystem.clamp_to_screen(2000, 1200)
        check("clamp_to_screen caps x at screen width-2",  x <= 1918)
        check("clamp_to_screen caps y at screen height-2", y <= 1078)

        x2, y2 = FailSafeSystem.clamp_to_screen(-10, -5)
        check("clamp_to_screen floors x at 1", x2 >= 1)
        check("clamp_to_screen floors y at 1", y2 >= 1)

        x3, y3 = FailSafeSystem.clamp_to_screen(500, 400)
        check("clamp_to_screen leaves valid coords unchanged",
              x3 == 500 and y3 == 400)


# ─────────────────────────────────────────────────────────────────────────────
# 2. CCPermissionManager
# ─────────────────────────────────────────────────────────────────────────────

def test_cc_permissions():
    console.print("\n[bold cyan]── 2. CCPermissionManager ──────────────────────────────[/bold cyan]")
    pm = CCPermissionManager()

    # SAFE → auto-approved
    a_safe = _action(risk=ActionRisk.SAFE)
    check("SAFE risk auto-approved", pm.request(a_safe))
    check("SAFE approved_by == 'auto'", a_safe.approved_by == "auto")

    # MEDIUM → auto-approved
    a_med = _action(risk=ActionRisk.MEDIUM)
    check("MEDIUM risk auto-approved", pm.request(a_med))

    # HIGH → now auto-approved (trusted desktop actions)
    a_high = _action(risk=ActionRisk.HIGH)
    check("HIGH risk auto-approved", pm.request(a_high))
    check("HIGH approved_by == 'auto'", a_high.approved_by == "auto")

    # CRITICAL → always denied
    a_crit = _action(risk=ActionRisk.CRITICAL)
    check("CRITICAL risk denied", not pm.request(a_crit))
    check("CRITICAL status == DENIED", a_crit.status == ActionStatus.DENIED)

    # Override DENY
    pm.set_override("mouse", "move_to", CCPermissionMode.DENY)
    a_deny = _action(ControllerType.MOUSE, "move_to", risk=ActionRisk.MEDIUM)
    check("override DENY blocks action", not pm.request(a_deny))

    # Override ALLOW
    pm2 = CCPermissionManager()
    pm2.set_override("keyboard", "type_text", CCPermissionMode.ALLOW)
    a_allow = _action(ControllerType.KEYBOARD, "type_text", risk=ActionRisk.HIGH)
    check("override ALLOW approves HIGH risk", pm2.request(a_allow))

    # Session allow
    pm3 = CCPermissionManager()
    pm3.allow_session("app", "open_app")
    a_sess = _action(ControllerType.APP, "open_app", risk=ActionRisk.HIGH)
    check("session allow approves without prompt", pm3.request(a_sess))
    check("session approved_by == 'session'", a_sess.approved_by == "session")


# ─────────────────────────────────────────────────────────────────────────────
# 3. ControlAction lifecycle & serialisation
# ─────────────────────────────────────────────────────────────────────────────

def test_control_action():
    console.print("\n[bold cyan]── 3. ControlAction Lifecycle ──────────────────────────[/bold cyan]")

    a = _action()
    check("initial status PENDING", a.status == ActionStatus.PENDING)
    check("action_id auto-generated", bool(a.action_id))

    a.mark_running()
    check("mark_running → RUNNING", a.status == ActionStatus.RUNNING)
    check("started_at set", a.started_at is not None)

    a.mark_success("done")
    check("mark_success → SUCCESS", a.status == ActionStatus.SUCCESS)
    check("output stored", a.output == "done")
    check("duration_ms set", a.duration_ms is not None and a.duration_ms >= 0)

    a2 = _action()
    a2.mark_running()
    a2.mark_failed("oops")
    check("mark_failed → FAILED", a2.status == ActionStatus.FAILED)
    check("error stored", a2.error == "oops")

    a3 = _action()
    a3.mark_denied()
    check("mark_denied → DENIED", a3.status == ActionStatus.DENIED)

    a4 = _action()
    a4.mark_cancelled()
    check("mark_cancelled → CANCELLED", a4.status == ActionStatus.CANCELLED)

    # Serialisation
    d = a.to_dict()
    check("to_dict has action_id",   "action_id"   in d)
    check("to_dict has controller",  "controller"  in d)
    check("to_dict has status",      d["status"]   == "success")
    check("to_dict has risk",        "risk"        in d)
    check("to_dict has duration_ms", d["duration_ms"] is not None)

    # ControlResult
    r = ControlResult(session_id="s1", goal="test")
    r.actions.extend([a, a2, a3])
    check("ControlResult success_count == 1", r.success_count == 1)
    check("ControlResult failed_count == 1",  r.failed_count  == 1)
    check("ControlResult denied_count == 1",  r.denied_count  == 1)
    check("ControlResult all_succeeded False", not r.all_succeeded)


# ─────────────────────────────────────────────────────────────────────────────
# 4. ActionQueue
# ─────────────────────────────────────────────────────────────────────────────

def test_action_queue():
    console.print("\n[bold cyan]── 4. ActionQueue ──────────────────────────────────────[/bold cyan]")

    # Basic enqueue + run
    q = ActionQueue(action_delay_s=0)
    a1 = _action(desc="step1")
    a2 = _action(desc="step2")
    q.enqueue(a1)
    q.enqueue(a2)
    check("pending_count == 2", q.pending_count() == 2)

    def _ok_executor(action: ControlAction) -> str:
        return f"executed {action.description}"

    result = q.run(_ok_executor, session_id="q-test", goal="test queue")
    check("both actions succeed", result.success_count == 2)
    check("queue drained after run", q.pending_count() == 0)
    check("completed_count == 2", q.completed_count() == 2)

    # Failure + retry
    q2 = ActionQueue(action_delay_s=0, max_retries=1)
    call_count = {"n": 0}

    def _fail_once(action: ControlAction) -> str:
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise RuntimeError("transient error")
        return "recovered"

    a3 = _action(desc="retry_step")
    q2.enqueue(a3)
    result2 = q2.run(_fail_once)
    check("retry recovers on second attempt", result2.success_count == 1)
    check("retry called executor twice", call_count["n"] == 2)

    # Permanent failure
    q3 = ActionQueue(action_delay_s=0, max_retries=0)

    def _always_fail(action: ControlAction) -> str:
        raise RuntimeError("permanent error")

    a4 = _action(desc="fail_step")
    q3.enqueue(a4)
    result3 = q3.run(_always_fail)
    check("permanent failure recorded", result3.failed_count == 1)
    check("get_failed returns 1", len(q3.get_failed()) == 1)

    # Emergency stop via fail-safe
    from computer_control.failsafe import failsafe as _fs
    q4 = ActionQueue(action_delay_s=0)
    q4.enqueue(_action(desc="before_stop"))
    q4.enqueue(_action(desc="after_stop"))

    _fs.trigger_stop()

    def _normal_executor(action: ControlAction) -> str:
        return "ok"

    result4 = q4.run(_normal_executor)
    _fs.reset()
    cancelled = sum(1 for a in result4.actions if a.status == ActionStatus.CANCELLED)
    check("fail-safe cancels remaining actions", cancelled >= 1)

    # Summary
    summary = q.summary()
    check("summary has 'total' key",   "total"   in summary)
    check("summary has 'success' key", "success" in summary)
    check("summary has 'failed' key",  "failed"  in summary)


# ─────────────────────────────────────────────────────────────────────────────
# 5. MouseController (mocked pyautogui)
# ─────────────────────────────────────────────────────────────────────────────

def test_mouse_controller():
    console.print("\n[bold cyan]── 5. MouseController ──────────────────────────────────[/bold cyan]")
    from computer_control.mouse_controller import MouseController
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    mock_pag = MagicMock()
    mock_pag.size.return_value = (1920, 1080)
    mock_pag.position.return_value = MagicMock(x=500, y=400)
    mock_pag.easeInOutQuad = None

    mc = MouseController()
    mc._pag = mock_pag

    out = mc.move_to(500, 300)
    check("move_to returns message", "moved" in out.lower() or "500" in out)
    check("move_to calls moveTo", mock_pag.moveTo.called)

    out2 = mc.click(200, 200)
    check("click returns message", "click" in out2.lower() or "200" in out2)
    check("click calls click()", mock_pag.click.called)

    out3 = mc.double_click(300, 300)
    check("double_click returns message", "double" in out3.lower() or "300" in out3)

    out4 = mc.right_click(400, 400)
    check("right_click returns message", "right" in out4.lower() or "400" in out4)

    out5 = mc.scroll(clicks=3)
    check("scroll returns message", "scroll" in out5.lower())

    out6 = mc.get_position()
    check("get_position returns position string", "position" in out6.lower() or "500" in out6)

    # Unsupported action raises
    try:
        mc.execute("teleport", {})
        check("unsupported action raises ValueError", False)
    except ValueError:
        check("unsupported action raises ValueError", True)

    # Supported actions list
    check("move_to in SUPPORTED_ACTIONS",    "move_to"      in mc.SUPPORTED_ACTIONS)
    check("click in SUPPORTED_ACTIONS",      "click"        in mc.SUPPORTED_ACTIONS)
    check("scroll in SUPPORTED_ACTIONS",     "scroll"       in mc.SUPPORTED_ACTIONS)
    check("get_position in SUPPORTED_ACTIONS", "get_position" in mc.SUPPORTED_ACTIONS)


# ─────────────────────────────────────────────────────────────────────────────
# 6. KeyboardController (mocked pyautogui)
# ─────────────────────────────────────────────────────────────────────────────

def test_keyboard_controller():
    console.print("\n[bold cyan]── 6. KeyboardController ───────────────────────────────[/bold cyan]")
    from computer_control.keyboard_controller import KeyboardController, MAX_TEXT_LENGTH
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    mock_pag = MagicMock()
    kc = KeyboardController()
    kc._pag = mock_pag

    out = kc.type_text("Hello JARVIS")
    check("type_text returns message", "typed" in out.lower() or "hello" in out.lower())
    check("type_text calls typewrite", mock_pag.typewrite.called)

    out2 = kc.press("enter")
    check("press returns message", "enter" in out2.lower() or "pressed" in out2.lower())
    check("press calls press()", mock_pag.press.called)

    out3 = kc.hotkey("ctrl", "s")
    check("hotkey ctrl+s returns message", "ctrl" in out3.lower() or "hotkey" in out3.lower())
    check("hotkey calls hotkey()", mock_pag.hotkey.called)

    # Blocked hotkey
    try:
        kc.hotkey("alt", "f4")
        check("blocked hotkey raises ValueError", False)
    except ValueError:
        check("blocked hotkey raises ValueError", True)

    # Text too long
    try:
        kc.type_text("x" * (MAX_TEXT_LENGTH + 1))
        check("oversized text raises ValueError", False)
    except ValueError:
        check("oversized text raises ValueError", True)

    # clear_field
    out4 = kc.clear_field()
    check("clear_field returns message", "clear" in out4.lower())

    # Unsupported action
    try:
        kc.execute("inject_code", {})
        check("unsupported action raises ValueError", False)
    except ValueError:
        check("unsupported action raises ValueError", True)


# ─────────────────────────────────────────────────────────────────────────────
# 7. ScreenshotManager (mocked pyautogui)
# ─────────────────────────────────────────────────────────────────────────────

def test_screenshot_manager():
    console.print("\n[bold cyan]── 7. ScreenshotManager ────────────────────────────────[/bold cyan]")
    from computer_control.screenshot_manager import ScreenshotManager
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    tmp_dir = Path(tempfile.mkdtemp(prefix="jarvis_ss_test_"))
    sm = ScreenshotManager(screenshot_dir=tmp_dir)

    # Mock pyautogui.screenshot to return a real Pillow image
    from PIL import Image
    fake_img = Image.new("RGB", (100, 100), color=(128, 64, 32))

    with patch("pyautogui.screenshot", return_value=fake_img):
        path = sm.capture_screen(suffix="test")
        check("capture_screen returns path string", isinstance(path, str))
        check("screenshot file created", Path(path).exists())

        path2 = sm.capture_region(0, 0, 100, 100, suffix="region")
        check("capture_region returns path string", isinstance(path2, str))
        check("region screenshot file created", Path(path2).exists())

    latest = sm.get_latest()
    check("get_latest returns a path", len(latest) > 0 and "No" not in latest)

    listing = sm.list_screenshots()
    check("list_screenshots returns string", isinstance(listing, str))
    check("list_screenshots mentions count", "screenshot" in listing.lower() or "png" in listing.lower())

    # Unsupported action
    try:
        sm.execute("delete_all", {})
        check("unsupported action raises ValueError", False)
    except ValueError:
        check("unsupported action raises ValueError", True)

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 8. WindowManager (mocked pygetwindow)
# ─────────────────────────────────────────────────────────────────────────────

def test_window_manager():
    console.print("\n[bold cyan]── 8. WindowManager ────────────────────────────────────[/bold cyan]")
    from computer_control.window_manager import WindowManager
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    # Build mock windows
    def _mock_win(title: str):
        w = MagicMock()
        w.title = title
        return w

    mock_wins = [
        _mock_win("Google Chrome"),
        _mock_win("Visual Studio Code"),
        _mock_win("Windows Explorer"),
        _mock_win(""),   # empty title — should be filtered
    ]

    mock_gw = MagicMock()
    mock_gw.getAllTitles.return_value = [w.title for w in mock_wins]
    mock_gw.getAllWindows.return_value = mock_wins
    mock_gw.getActiveWindow.return_value = mock_wins[0]

    wm = WindowManager()
    wm._gw = mock_gw

    listing = wm.list_windows()
    check("list_windows returns string", isinstance(listing, str))
    check("list_windows contains Chrome", "Chrome" in listing)
    check("list_windows filters empty titles", "" not in listing.split("•"))

    out = wm.focus_window("Chrome")
    check("focus_window returns message", "focus" in out.lower() or "chrome" in out.lower())

    out2 = wm.maximize_window("Code")
    check("maximize_window returns message", "maxim" in out2.lower() or "code" in out2.lower())

    out3 = wm.minimize_window("Explorer")
    check("minimize_window returns message", "minim" in out3.lower() or "explorer" in out3.lower())

    out4 = wm.get_active_window()
    check("get_active_window returns string", "active" in out4.lower() or "chrome" in out4.lower())

    out5 = wm.window_exists("Chrome")
    check("window_exists True for Chrome", "True" in out5)

    out6 = wm.window_exists("Nonexistent App XYZ")
    check("window_exists False for missing", "False" in out6)

    # Missing window raises
    try:
        wm.focus_window("Nonexistent App XYZ 999")
        check("focus missing window raises ValueError", False)
    except ValueError:
        check("focus missing window raises ValueError", True)


# ─────────────────────────────────────────────────────────────────────────────
# 9. AppController (mocked subprocess + psutil)
# ─────────────────────────────────────────────────────────────────────────────

def test_app_controller():
    console.print("\n[bold cyan]── 9. AppController ────────────────────────────────────[/bold cyan]")
    from computer_control.app_controller import AppController, SAFE_APPS
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    ac = AppController()

    # Whitelist check
    check("'notepad' in SAFE_APPS",    "notepad" in SAFE_APPS)
    check("'chrome' in SAFE_APPS",     "chrome"  in SAFE_APPS)
    check("'vscode' in SAFE_APPS",     "vscode"  in SAFE_APPS)
    check("'calculator' in SAFE_APPS", "calculator" in SAFE_APPS)

    # Unlisted app returns appropriate message
    out = ac.open_app("malware.exe")
    check("unlisted app returns message", "Could not find" in out or "not found" in out)

    # open_app with mocked subprocess
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = MagicMock()
        out = ac.open_app("notepad")
        check("open_app returns message", "launch" in out.lower() or "notepad" in out.lower())
        check("open_app calls Popen", mock_popen.called)

    # is_running with mocked psutil
    mock_proc = MagicMock()
    mock_proc.info = {"name": "notepad.exe"}
    with patch("psutil.process_iter", return_value=[mock_proc]):
        out2 = ac.is_running("notepad")
        check("is_running detects running process", "running" in out2.lower())

    # is_running when not running
    with patch("psutil.process_iter", return_value=[]):
        out3 = ac.is_running("notepad")
        check("is_running returns NOT running", "not" in out3.lower())

    # list_running
    with patch("psutil.process_iter", return_value=[mock_proc]):
        out4 = ac.list_running()
        check("list_running returns string", isinstance(out4, str))


# ─────────────────────────────────────────────────────────────────────────────
# 10. BrowserController (mocked pyautogui + webbrowser)
# ─────────────────────────────────────────────────────────────────────────────

def test_browser_controller():
    console.print("\n[bold cyan]── 10. BrowserController ───────────────────────────────[/bold cyan]")
    from computer_control.browser_controller import BrowserController
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    mock_pag = MagicMock()
    bc = BrowserController()
    bc._pag = mock_pag

    with patch("webbrowser.open") as mock_wb, \
         patch("time.sleep"):
        out = bc.open_url("https://google.com")
        check("open_url returns message", "opened" in out.lower() or "google" in out.lower())
        check("open_url calls webbrowser.open", mock_wb.called)

        out2 = bc.search_google("latest AI models")
        check("search_google returns message", "search" in out2.lower() or "google" in out2.lower())

        out3 = bc.search_bing("JARVIS AI")
        check("search_bing returns message", "bing" in out3.lower() or "search" in out3.lower())

    with patch("time.sleep"):
        out4 = bc.new_tab()
        check("new_tab returns message", "tab" in out4.lower())
        check("new_tab calls hotkey ctrl+t", mock_pag.hotkey.called)

        out5 = bc.close_tab()
        check("close_tab returns message", "tab" in out5.lower() or "close" in out5.lower())

        out6 = bc.refresh_page()
        check("refresh_page returns message", "refresh" in out6.lower())

        out7 = bc.scroll_page(clicks=-3)
        check("scroll_page returns message", "scroll" in out7.lower())

        out8 = bc.go_back()
        check("go_back returns message", "back" in out8.lower())

        out9 = bc.go_forward()
        check("go_forward returns message", "forward" in out9.lower())

    # Unsupported action
    try:
        bc.execute("hack_browser", {})
        check("unsupported action raises ValueError", False)
    except ValueError:
        check("unsupported action raises ValueError", True)

    # Supported actions declared
    check("open_url in SUPPORTED_ACTIONS",      "open_url"      in bc.SUPPORTED_ACTIONS)
    check("search_google in SUPPORTED_ACTIONS", "search_google" in bc.SUPPORTED_ACTIONS)
    check("new_tab in SUPPORTED_ACTIONS",       "new_tab"       in bc.SUPPORTED_ACTIONS)


# ─────────────────────────────────────────────────────────────────────────────
# 11. UILocator (mocked pyautogui)
# ─────────────────────────────────────────────────────────────────────────────

def test_ui_locator():
    console.print("\n[bold cyan]── 11. UILocator ───────────────────────────────────────[/bold cyan]")
    from computer_control.ui_locator import UILocator
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    tmp_dir = Path(tempfile.mkdtemp(prefix="jarvis_ui_test_"))
    ul = UILocator(templates_dir=tmp_dir)

    # Create a dummy template image
    from PIL import Image
    dummy = Image.new("RGB", (50, 50), color=(255, 0, 0))
    template_path = tmp_dir / "test_button.png"
    dummy.save(str(template_path))

    # locate_image — found
    mock_location = MagicMock()
    mock_location.left = 100; mock_location.top = 200
    mock_location.width = 50; mock_location.height = 50

    with patch("pyautogui.locateOnScreen", return_value=mock_location):
        out = ul.locate_image("test_button.png")
        check("locate_image found returns message", "found" in out.lower() or "100" in out)

    # locate_image — not found
    with patch("pyautogui.locateOnScreen", return_value=None):
        out2 = ul.locate_image("test_button.png")
        check("locate_image not found returns message", "not found" in out2.lower())

    # image_exists — True
    with patch("pyautogui.locateOnScreen", return_value=mock_location):
        out3 = ul.image_exists("test_button.png")
        check("image_exists True when found", "True" in out3)

    # image_exists — False
    with patch("pyautogui.locateOnScreen", return_value=None):
        out4 = ul.image_exists("test_button.png")
        check("image_exists False when not found", "False" in out4)

    # locate_and_click — found
    mock_center = MagicMock()
    with patch("pyautogui.locateOnScreen", return_value=mock_location), \
         patch("pyautogui.center", return_value=mock_center), \
         patch("pyautogui.click"):
        out5 = ul.locate_and_click("test_button.png")
        check("locate_and_click returns message", "click" in out5.lower())

    # locate_and_click — not found raises
    with patch("pyautogui.locateOnScreen", return_value=None):
        try:
            ul.locate_and_click("test_button.png")
            check("locate_and_click not found raises", False)
        except RuntimeError:
            check("locate_and_click not found raises", True)

    # wait_for_image — appears immediately
    with patch("pyautogui.locateOnScreen", return_value=mock_location):
        out6 = ul.wait_for_image("test_button.png", timeout_s=2)
        check("wait_for_image found returns message", "appeared" in out6.lower())

    # wait_for_image — timeout
    with patch("pyautogui.locateOnScreen", return_value=None):
        out7 = ul.wait_for_image("test_button.png", timeout_s=0.1)
        check("wait_for_image timeout returns message", "timeout" in out7.lower())

    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 12. ScreenAnalyzer (mocked pyautogui + real PIL)
# ─────────────────────────────────────────────────────────────────────────────

def test_screen_analyzer():
    console.print("\n[bold cyan]── 12. ScreenAnalyzer ──────────────────────────────────[/bold cyan]")
    from computer_control.screen_analyzer import ScreenAnalyzer
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    sa = ScreenAnalyzer()

    # get_screen_info
    with patch("pyautogui.size", return_value=(1920, 1080)):
        out = sa.get_screen_info()
        check("get_screen_info returns resolution", "1920" in out and "1080" in out)

    # get_pixel_color
    with patch("pyautogui.size", return_value=(1920, 1080)), \
         patch("pyautogui.pixel", return_value=(255, 128, 0)):
        out2 = sa.get_pixel_color(500, 300)
        check("get_pixel_color returns RGB", "255" in out2 or "RGB" in out2)

    # detect_windows
    mock_gw = MagicMock()
    mock_gw.getAllTitles.return_value = ["Chrome", "VS Code", ""]
    mock_gw.getAllWindows.return_value = []
    with patch("pygetwindow.getAllTitles", return_value=["Chrome", "VS Code", ""]):
        out3 = sa.detect_windows()
        check("detect_windows returns string", isinstance(out3, str))

    # analyze_screenshot — real PIL image
    tmp = Path(tempfile.mkdtemp(prefix="jarvis_sa_test_"))
    from PIL import Image
    img = Image.new("RGB", (200, 150), color=(100, 150, 200))
    img_path = tmp / "test_shot.png"
    img.save(str(img_path))

    out4 = sa.analyze_screenshot(str(img_path))
    check("analyze_screenshot returns dimensions", "200" in out4 and "150" in out4)
    check("analyze_screenshot returns file size",  "KB" in out4)
    check("analyze_screenshot returns avg color",  "RGB" in out4 or "color" in out4.lower())

    # analyze_screenshot — missing file
    out5 = sa.analyze_screenshot("/nonexistent/path/shot.png")
    check("analyze_screenshot missing file returns message", "not found" in out5.lower())

    # add_analyzer extension point
    called = {"yes": False}
    def _custom_fn(img, path):
        called["yes"] = True
        return "custom analysis done"

    sa.add_analyzer("test_analyzer", _custom_fn)
    sa.analyze_screenshot(str(img_path))
    check("custom analyzer called via add_analyzer", called["yes"])

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 13. ControlManager — dispatch + workflow + logging
# ─────────────────────────────────────────────────────────────────────────────

def test_control_manager():
    console.print("\n[bold cyan]── 13. ControlManager ──────────────────────────────────[/bold cyan]")
    from computer_control.control_manager import ControlManager
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    # Build manager with all-ALLOW permission manager
    pm = CCPermissionManager()
    for ctrl in ("mouse", "keyboard", "window", "browser", "app", "screen", "screenshot", "ui"):
        for act in ("move_to", "click", "type_text", "press", "hotkey",
                    "get_active_window", "list_windows", "get_screen_info",
                    "capture_screen", "open_url", "search_google",
                    "open_app", "wait_for_app", "is_running"):
            pm.set_override(ctrl, act, CCPermissionMode.ALLOW)

    tmp_log = Path(tempfile.mkdtemp(prefix="jarvis_cm_test_"))
    cm = ControlManager(permission_manager=pm)
    cm._log_dir = tmp_log

    # Mock all controllers
    mock_ctrl = MagicMock()
    mock_ctrl.execute.return_value = "mock output"
    for key in list(cm._controllers.keys()):
        cm._controllers[key] = mock_ctrl

    # execute_actions — single SAFE action
    a1 = _action(ControllerType.SCREEN, "get_screen_info", {}, ActionRisk.SAFE)
    result = cm.execute_actions([a1], goal="test dispatch")
    check("execute_actions returns ControlResult", isinstance(result, ControlResult))
    check("single action succeeds", result.success_count == 1)
    check("mock controller called", mock_ctrl.execute.called)

    # execute_actions — multiple actions
    mock_ctrl.reset_mock()
    mock_ctrl.execute.return_value = "ok"
    actions = [
        _action(ControllerType.SCREEN,   "get_screen_info", {}, ActionRisk.SAFE),
        _action(ControllerType.MOUSE,    "move_to", {"x": 100, "y": 100}, ActionRisk.MEDIUM),
        _action(ControllerType.KEYBOARD, "press",   {"key": "enter"},     ActionRisk.HIGH),
    ]
    result2 = cm.execute_actions(actions, goal="multi action test")
    check("3 actions all succeed", result2.success_count == 3)

    # CRITICAL action is denied before queuing
    a_crit = _action(risk=ActionRisk.CRITICAL)
    result3 = cm.execute_actions([a_crit], goal="critical test")
    check("CRITICAL action denied", result3.denied_count == 1)
    check("CRITICAL action not executed", result3.success_count == 0)

    # Log file written
    import time as _time
    _time.sleep(0.05)
    log_files = list(tmp_log.glob("*.jsonl"))
    check("control log file created", len(log_files) > 0)

    # Workflow list
    available = [
        n.replace("_workflow_", "")
        for n in dir(cm) if n.startswith("_workflow_")
    ]
    check("open_chrome_and_search workflow exists",
          "open_chrome_and_search" in available)
    check("screenshot_workflow exists",
          "screenshot_workflow" in available)
    check("open_app_workflow exists",
          "open_app_workflow" in available)
    check("create_notepad_file workflow exists",
          "create_notepad_file" in available)

    # Unknown workflow raises
    try:
        cm.run_workflow("nonexistent_workflow_xyz")
        check("unknown workflow raises ValueError", False)
    except ValueError:
        check("unknown workflow raises ValueError", True)

    import shutil
    shutil.rmtree(tmp_log, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# 14. Full workflow: open_chrome_and_search (mocked)
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_open_chrome_search():
    console.print("\n[bold cyan]── 14. Workflow: open_chrome_and_search ────────────────[/bold cyan]")
    from computer_control.control_manager import ControlManager
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    pm = CCPermissionManager()
    for ctrl in ("app", "browser", "window", "screen"):
        for act in ("open_app", "wait_for_app", "search_google",
                    "get_active_window", "get_screen_info"):
            pm.set_override(ctrl, act, CCPermissionMode.ALLOW)

    cm = ControlManager(permission_manager=pm)
    mock_ctrl = MagicMock()
    mock_ctrl.execute.return_value = "mock ok"
    for key in list(cm._controllers.keys()):
        cm._controllers[key] = mock_ctrl

    result = cm.run_workflow("open_chrome_and_search", query="latest AI models")
    check("workflow returns ControlResult", isinstance(result, ControlResult))
    check("workflow has 3 steps", len(result.actions) == 3)
    check("all steps succeed", result.success_count == 3)
    check("no failures", result.failed_count == 0)

    # Verify step descriptions
    descs = [a.description for a in result.actions]
    check("step 1 launches Chrome",
          any("chrome" in d.lower() or "launch" in d.lower() for d in descs))
    check("step 2 waits for Chrome",
          any("wait" in d.lower() for d in descs))
    check("step 3 searches Google",
          any("search" in d.lower() or "google" in d.lower() for d in descs))


# ─────────────────────────────────────────────────────────────────────────────
# 15. Full workflow: screenshot_workflow (mocked)
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_screenshot():
    console.print("\n[bold cyan]── 15. Workflow: screenshot_workflow ───────────────────[/bold cyan]")
    from computer_control.control_manager import ControlManager
    from computer_control.failsafe import failsafe as _fs
    _fs.disable()

    pm = CCPermissionManager()
    pm.set_override("screen",      "get_screen_info", CCPermissionMode.ALLOW)
    pm.set_override("screenshot",  "capture_screen",  CCPermissionMode.ALLOW)

    cm = ControlManager(permission_manager=pm)
    mock_ctrl = MagicMock()
    mock_ctrl.execute.return_value = "screenshot saved"
    for key in list(cm._controllers.keys()):
        cm._controllers[key] = mock_ctrl

    result = cm.run_workflow("screenshot_workflow")
    check("screenshot workflow returns ControlResult", isinstance(result, ControlResult))
    check("screenshot workflow has 2 steps", len(result.actions) == 2)
    check("both steps succeed", result.success_count == 2)

    # Verify controllers used
    controllers_used = {a.controller.value for a in result.actions}
    check("screen controller used",      "screen"     in controllers_used)
    check("screenshot controller used",  "screenshot" in controllers_used)

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_failsafe()
    test_cc_permissions()
    test_control_action()
    test_action_queue()
    test_mouse_controller()
    test_keyboard_controller()
    test_screenshot_manager()
    test_window_manager()
    test_app_controller()
    test_browser_controller()
    test_ui_locator()
    test_screen_analyzer()
    test_control_manager()
    test_workflow_open_chrome_search()
    test_workflow_screenshot()

    total = _results["pass"] + _results["fail"]
    console.print(f"\n{'═' * 60}")
    console.print(
        f"  Results: [green]{_results['pass']}[/green]/{total} passed  "
        f"([red]{_results['fail']}[/red] failed)"
    )
    console.print(f"{'═' * 60}\n")

    sys.exit(0 if _results["fail"] == 0 else 1)
