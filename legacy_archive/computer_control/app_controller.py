"""
app_controller.py
=================
AppController — launch, detect, and close applications safely.

Now backed by AppRegistry for dynamic alias resolution.
Any app registered in app_registry.py can be launched by alias.
Unknown apps are handled gracefully — no crash, just a clear message.
"""

from __future__ import annotations

import logging
import subprocess
import time
from typing import Optional

import psutil

from computer_control.cc_models import ActionRisk
from computer_control.failsafe import failsafe
from computer_control.app_registry import app_registry, AppRegistry

logger = logging.getLogger(__name__)

DEFAULT_WAIT_TIMEOUT_S = 10

# Backwards compatibility for tests expecting SAFE_APPS
SAFE_APPS = {
    entry.canonical: entry.executable
    for entry in app_registry._entries.values()
}


class AppController:
    """
    Launches and manages applications via the AppRegistry.

    Usage
    -----
    app_controller.open_app("brave")
    app_controller.open_app("discord")
    app_controller.is_running("spotify")
    """

    SUPPORTED_ACTIONS = [
        "open_app", "close_app", "is_running", "list_running", "wait_for_app",
    ]

    ACTION_RISK = {
        "open_app":     ActionRisk.HIGH,
        "close_app":    ActionRisk.HIGH,
        "is_running":   ActionRisk.SAFE,
        "list_running": ActionRisk.SAFE,
        "wait_for_app": ActionRisk.SAFE,
    }

    def __init__(self, registry: Optional[AppRegistry] = None) -> None:
        self._registry = registry or app_registry

    # ── Public actions ─────────────────────────────────────────────────────────

    def open_app(self, app_name: str) -> str:
        """
        Launch an application by name or alias.
        Returns a clear message if the app is not found — never crashes.
        """
        failsafe.check()

        canonical, executable = self._registry.resolve(app_name)

        if canonical is None:
            # Graceful unknown-app handling
            msg = (
                f"Could not find application: {app_name!r}. "
                f"Available: {', '.join(self._registry.list_apps()[:15])}..."
            )
            logger.warning(f"AppController: {msg}")
            return msg

        try:
            subprocess.Popen(
                executable,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"AppController: launched {canonical!r} ({executable!r})")
            return f"Launched: {canonical!r} ({executable})"

        except Exception as exc:
            err = f"Failed to launch {app_name!r}: {exc}"
            logger.error(f"AppController: {err}")
            return err   # return instead of raise so workflow continues

    def close_app(self, app_name: str) -> str:
        """Terminate processes matching app_name — HIGH risk."""
        failsafe.check()

        canonical, executable = self._registry.resolve(app_name)
        if canonical is None:
            return f"Cannot close {app_name!r}: not found in registry"

        # Strip .exe for psutil name matching
        proc_name = executable.replace(".exe", "").lower()
        killed = 0
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                if proc_name in proc.info["name"].lower():
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if killed == 0:
            return f"No running process found for {app_name!r}"
        logger.info(f"AppController: terminated {killed} process(es) for {canonical!r}")
        return f"Closed {killed} process(es) for {canonical!r}"

    def is_running(self, app_name: str) -> str:
        canonical, executable = self._registry.resolve(app_name)
        if canonical is None:
            return f"{app_name!r} is NOT running (not in registry)"

        proc_name = executable.replace(".exe", "").lower()
        for proc in psutil.process_iter(["name"]):
            try:
                if proc_name in proc.info["name"].lower():
                    return f"{canonical!r} is running"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return f"{canonical!r} is NOT running"

    def list_running(self) -> str:
        running = set()
        for proc in psutil.process_iter(["name"]):
            try:
                pname = proc.info["name"].lower().replace(".exe", "")
                for canonical, entry in self._registry._entries.items():
                    exe_stem = entry.executable.replace(".exe", "").lower()
                    if pname == exe_stem or exe_stem in pname:
                        running.add(canonical)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if not running:
            return "No registered apps currently running"
        return "Running apps: " + ", ".join(sorted(running))

    def wait_for_app(
        self,
        app_name: str,
        timeout_s: float = DEFAULT_WAIT_TIMEOUT_S,
    ) -> str:
        """Wait until the app is detected as running (polls every 0.5s)."""
        failsafe.check()
        start = time.time()
        while time.time() - start < timeout_s:
            failsafe.check()
            result = self.is_running(app_name)
            if "is running" in result:
                return f"{app_name!r} is ready"
            time.sleep(0.5)
        return f"Timeout: {app_name!r} did not start within {timeout_s}s"

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def execute(self, action: str, params: dict) -> str:
        if action not in self.SUPPORTED_ACTIONS:
            raise ValueError(f"AppController: unsupported action {action!r}")
        method = getattr(self, action)
        return method(**params)
