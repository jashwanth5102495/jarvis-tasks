"""
control_manager.py
==================
ControlManager — central orchestrator for all desktop control.

Pipeline
--------
  Goal / action list
       ↓
  CCPermissionManager.request(action)   ← permission gate
       ↓ approved
  ControlManager._dispatch(action)      ← routes to correct controller
       ↓
  ScreenshotManager (before/after)      ← optional visual logging
       ↓
  ControlLogger.record(action)          ← persistence
       ↓
  Console UX                            ← rich output

Controller registry
-------------------
  "mouse"    → MouseController
  "keyboard" → KeyboardController
  "window"   → WindowManager
  "browser"  → BrowserController
  "app"      → AppController
  "screen"   → ScreenAnalyzer
  "screenshot" → ScreenshotManager
  "ui"       → UILocator

Predefined workflows
--------------------
  open_chrome_and_search(query)
  open_app_workflow(app_name)
  create_notepad_file(content, filename)
  browser_search_workflow(query, engine)

Usage
-----
    result = control_manager.execute_actions(actions)
    result = control_manager.run_workflow("open_chrome_and_search",
                                          query="latest AI models")
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from computer_control.action_queue import ActionQueue
from computer_control.app_controller import AppController
from computer_control.browser_controller import BrowserController
from computer_control.cc_models import (
    ActionRisk, ActionStatus, ControlAction, ControlResult, ControllerType
)
from computer_control.cc_permissions import CCPermissionManager, cc_permission_manager
from computer_control.failsafe import FailSafeTriggered, failsafe
from computer_control.keyboard_controller import KeyboardController
from computer_control.mouse_controller import MouseController
from computer_control.screen_analyzer import ScreenAnalyzer
from computer_control.screenshot_manager import ScreenshotManager
from computer_control.ui_locator import UILocator
from computer_control.window_manager import WindowManager
from computer_control.action_translator import action_translator, TranslatedAction

logger = logging.getLogger(__name__)

_LOG_DIR = Path(__file__).parent.parent / "logs" / "control_logs"

try:
    from rich.console import Console
    from rich.panel import Panel
    _console = Console()
    _RICH = True
except ImportError:
    _RICH = False
    _console = None  # type: ignore


class ControlManager:
    """
    Central orchestrator for all desktop control actions.

    Usage
    -----
    result = control_manager.execute_actions([action1, action2])
    result = control_manager.run_workflow("open_chrome_and_search",
                                          query="AI news")
    """

    def __init__(
        self,
        permission_manager: Optional[CCPermissionManager] = None,
        take_screenshots: bool = False,
    ) -> None:
        self._pm              = permission_manager or cc_permission_manager
        self._take_screenshots = take_screenshots
        self._controllers: Dict[str, Any] = {}
        self._log_dir = _LOG_DIR
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._register_controllers()

    # ── Controller registry ────────────────────────────────────────────────────

    def _register_controllers(self) -> None:
        self._controllers = {
            ControllerType.MOUSE.value:       MouseController(),
            ControllerType.KEYBOARD.value:    KeyboardController(),
            ControllerType.WINDOW.value:      WindowManager(),
            ControllerType.BROWSER.value:     BrowserController(),
            ControllerType.APP.value:         AppController(),
            ControllerType.SCREEN.value:      ScreenAnalyzer(),
            ControllerType.SCREENSHOT.value:  ScreenshotManager(),
            ControllerType.UI.value:          UILocator(),
        }
        logger.info(f"ControlManager: registered {list(self._controllers.keys())}")

    def register_controller(self, name: str, controller: Any) -> None:
        self._controllers[name] = controller

    # ── Main entry points ──────────────────────────────────────────────────────

    def execute_actions(
        self,
        actions: List[ControlAction],
        goal: str = "",
        action_delay_s: float = 0.3,
    ) -> ControlResult:
        """
        Execute a list of ControlActions through the permission gate and queue.
        """
        session_id = str(uuid.uuid4())[:10]
        queue      = ActionQueue(action_delay_s=action_delay_s)

        self._print_header(goal or "Desktop Control Session", session_id, actions)

        # Permission gate — filter before queuing
        approved_actions: List[ControlAction] = []
        for action in actions:
            approved = self._pm.request(action)
            if approved:
                approved_actions.append(action)
            else:
                self._print_action_result(action)

        queue.enqueue_all(approved_actions)
        result = queue.run(
            executor_fn=self._dispatch,
            session_id=session_id,
            goal=goal,
        )

        # Add denied actions to result
        for action in actions:
            if action.status == ActionStatus.DENIED:
                result.actions.insert(0, action)

        self._print_summary(result)
        self._persist_log(result)
        return result

    def run_workflow(self, workflow_name: str, **kwargs) -> ControlResult:
        """
        Execute a named predefined workflow.

        Available workflows
        -------------------
        open_chrome_and_search(query)
        open_app_workflow(app_name)
        create_notepad_file(content, filename)
        browser_search_workflow(query, engine="google")
        screenshot_workflow()
        """
        builder = getattr(self, f"_workflow_{workflow_name}", None)
        if builder is None:
            available = [
                n.replace("_workflow_", "")
                for n in dir(self) if n.startswith("_workflow_")
            ]
            raise ValueError(
                f"Unknown workflow {workflow_name!r}. "
                f"Available: {available}"
            )
        actions = builder(**kwargs)
        return self.execute_actions(actions, goal=workflow_name)

    # ── Predefined workflows ───────────────────────────────────────────────────

    def _workflow_open_chrome_and_search(self, query: str) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.APP,
                action="open_app",
                params={"app_name": "chrome"},
                risk=ActionRisk.HIGH,
                description="Launch Google Chrome",
            ),
            ControlAction(
                controller=ControllerType.APP,
                action="wait_for_app",
                params={"app_name": "chrome", "timeout_s": 8},
                risk=ActionRisk.SAFE,
                description="Wait for Chrome to start",
            ),
            ControlAction(
                controller=ControllerType.BROWSER,
                action="search_google",
                params={"query": query},
                risk=ActionRisk.HIGH,
                description=f"Search Google: {query!r}",
            ),
        ]

    def _workflow_open_app_workflow(self, app_name: str) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.APP,
                action="open_app",
                params={"app_name": app_name},
                risk=ActionRisk.HIGH,
                description=f"Launch {app_name}",
            ),
            ControlAction(
                controller=ControllerType.APP,
                action="wait_for_app",
                params={"app_name": app_name, "timeout_s": 8},
                risk=ActionRisk.SAFE,
                description=f"Wait for {app_name} to start",
            ),
            ControlAction(
                controller=ControllerType.WINDOW,
                action="get_active_window",
                params={},
                risk=ActionRisk.SAFE,
                description="Confirm active window",
            ),
        ]

    def _workflow_create_notepad_file(
        self, content: str, filename: str = "jarvis_note.txt"
    ) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.APP,
                action="open_app",
                params={"app_name": "notepad"},
                risk=ActionRisk.HIGH,
                description="Open Notepad",
            ),
            ControlAction(
                controller=ControllerType.APP,
                action="wait_for_app",
                params={"app_name": "notepad", "timeout_s": 6},
                risk=ActionRisk.SAFE,
                description="Wait for Notepad",
            ),
            ControlAction(
                controller=ControllerType.KEYBOARD,
                action="type_text",
                params={"text": content, "interval": 0.03},
                risk=ActionRisk.HIGH,
                description=f"Type content into Notepad",
            ),
            ControlAction(
                controller=ControllerType.KEYBOARD,
                action="hotkey",
                params={"keys": ["ctrl", "s"]},
                risk=ActionRisk.HIGH,
                description="Save file (Ctrl+S)",
            ),
        ]

    def _workflow_browser_search_workflow(
        self, query: str, engine: str = "google"
    ) -> List[ControlAction]:
        action_name = "search_google" if engine.lower() == "google" else "search_bing"
        return [
            ControlAction(
                controller=ControllerType.BROWSER,
                action=action_name,
                params={"query": query},
                risk=ActionRisk.HIGH,
                description=f"{engine.title()} search: {query!r}",
            ),
        ]

    def _workflow_screenshot_workflow(self) -> List[ControlAction]:
        return [
            ControlAction(
                controller=ControllerType.SCREEN,
                action="get_screen_info",
                params={},
                risk=ActionRisk.SAFE,
                description="Get screen information",
            ),
            ControlAction(
                controller=ControllerType.SCREENSHOT,
                action="capture_screen",
                params={"suffix": "workflow"},
                risk=ActionRisk.SAFE,
                description="Capture full screen",
            ),
        ]

    # ── Semantic execution entry point ────────────────────────────────────────

    def execute_semantic(
        self,
        semantic_actions: List[tuple],
        goal: str = "",
        action_delay_s: float = 0.3,
    ) -> ControlResult:
        """
        Translate semantic action names and execute them.

        Parameters
        ----------
        semantic_actions : list of (semantic_name, params_dict) tuples
            e.g. [("move_to_center", {}), ("search_google", {"query": "AI"})]
        goal : str
            Human-readable goal for logging.
        action_delay_s : float
            Delay between actions.

        Returns
        -------
        ControlResult
        """
        translated = action_translator.translate_all(semantic_actions)
        if not translated:
            logger.warning("execute_semantic: no actions translated — nothing to execute")
            return ControlResult(session_id=str(uuid.uuid4())[:10], goal=goal)
        return self.execute_actions(translated, goal=goal, action_delay_s=action_delay_s)

    def execute_semantic_one(
        self,
        semantic_action: str,
        params: Optional[dict] = None,
        goal: str = "",
    ) -> ControlResult:
        """
        Translate and execute a single semantic action.

        Parameters
        ----------
        semantic_action : str
            e.g. "move_to_center", "search_google", "press_enter"
        params : dict, optional
            Extra parameters (e.g. {"query": "AI models"})
        """
        return self.execute_semantic(
            [(semantic_action, params or {})],
            goal=goal or semantic_action,
        )

    # ── Dispatcher ─────────────────────────────────────────────────────────────

    def _dispatch(self, action: ControlAction) -> str:
        """Route a ControlAction to the correct controller and execute it."""
        failsafe.check()

        controller = self._controllers.get(action.controller.value)
        if controller is None:
            raise ValueError(
                f"No controller registered for {action.controller.value!r}"
            )

        # Optional: screenshot before
        if self._take_screenshots:
            try:
                sc = self._controllers.get("screenshot")
                if sc:
                    path = sc.capture_screen(suffix="before")
                    action.screenshot_before = path
            except Exception:
                pass

        # Execute
        output = controller.execute(action.action, action.params)

        # Optional: screenshot after
        if self._take_screenshots:
            try:
                sc = self._controllers.get("screenshot")
                if sc:
                    path = sc.capture_screen(suffix="after")
                    action.screenshot_after = path
            except Exception:
                pass

        return output

    # ── Persistence ────────────────────────────────────────────────────────────

    def _persist_log(self, result: ControlResult) -> None:
        try:
            date_str  = datetime.now().strftime("%Y-%m-%d")
            log_file  = self._log_dir / f"{date_str}.jsonl"
            line      = json.dumps(result.to_dict(), ensure_ascii=False, default=str)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:
            logger.warning(f"ControlManager: log write failed: {exc}")

        # Best-effort MongoDB
        try:
            from database.mongodb import mongodb
            mongodb.insert_one("control_logs", result.to_dict())
        except Exception:
            pass

    # ── Console UX ─────────────────────────────────────────────────────────────

    def _print_header(
        self,
        goal: str,
        session_id: str,
        actions: List[ControlAction],
    ) -> None:
        controllers_used = sorted({a.controller.value for a in actions})
        if _RICH:
            _console.print()
            _console.print(Panel(
                f"[bold white]JARVIS Computer Control[/bold white]\n\n"
                f"  [dim]Session ID  :[/dim] [cyan]{session_id}[/cyan]\n"
                f"  [dim]Goal        :[/dim] [bold]{goal}[/bold]\n"
                f"  [dim]Actions     :[/dim] [cyan]{len(actions)}[/cyan]\n"
                f"  [dim]Controllers :[/dim] [green]{', '.join(controllers_used)}[/green]",
                border_style="bright_blue",
                expand=False,
            ))
        else:
            print(f"\n{'═' * 56}")
            print(f"  JARVIS Computer Control")
            print(f"  Session : {session_id}")
            print(f"  Goal    : {goal}")
            print(f"  Actions : {len(actions)}")
            print(f"{'═' * 56}")

    def _print_action_result(self, action: ControlAction) -> None:
        icons = {
            ActionStatus.SUCCESS:   ("✓", "green"),
            ActionStatus.FAILED:    ("✗", "red"),
            ActionStatus.DENIED:    ("⊘", "yellow"),
            ActionStatus.CANCELLED: ("⊙", "dim"),
        }
        icon, colour = icons.get(action.status, ("?", "white"))
        desc = action.description or f"{action.controller.value}.{action.action}"
        msg  = (action.output or action.error or action.status.value)[:100]

        if _RICH:
            _console.print(
                f"  [{colour}]{icon}  {action.status.value.upper():<10}[/{colour}]"
                f"  [bold]{desc}[/bold]  [dim]{msg}[/dim]"
            )
        else:
            print(f"  {icon}  {action.status.value.upper():<10}  {desc}  {msg}")

    def _print_summary(self, result: ControlResult) -> None:
        colour = "green" if result.all_succeeded else "yellow"
        if _RICH:
            _console.print()
            _console.print(Panel(
                f"[bold]Control Session Complete[/bold]\n\n"
                f"  [green]✓ Success  : {result.success_count}[/green]\n"
                f"  [red]✗ Failed   : {result.failed_count}[/red]\n"
                f"  [yellow]⊘ Denied   : {result.denied_count}[/yellow]",
                border_style=colour,
                expand=False,
            ))
        else:
            print(f"\n{'─' * 40}")
            print(f"  Control Session Complete")
            print(f"  ✓ Success : {result.success_count}")
            print(f"  ✗ Failed  : {result.failed_count}")
            print(f"  ⊘ Denied  : {result.denied_count}")
            print(f"{'─' * 40}\n")


# Module-level singleton
control_manager = ControlManager()
