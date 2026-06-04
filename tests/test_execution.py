"""
test_execution.py
=================
Automated test suite for the JARVIS Skill Execution Framework.

Covers
------
1.  Sandbox path validation
2.  FileExecutor — create / read / write / append / list / delete
3.  TerminalExecutor — safe commands, blocked commands, python check
4.  BrowserExecutor — URL validation, search
5.  CodingExecutor — project scaffolding, starter files
6.  PermissionManager — auto-approve, deny, blocked patterns
7.  ExecutionContext — lifecycle state machine
8.  ExecutionHistory — record and query
9.  TaskRouter — step generation per category
10. ExecutionManager — full pipeline (auto-approve mode)
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Isolate sandbox to a temp workspace for tests ─────────────────────────────
import tempfile
_TMP_DIR = tempfile.mkdtemp(prefix="jarvis_test_workspace_")

# Patch sandbox root BEFORE importing any executor
from skills.execution import sandbox as _sandbox_module
from skills.execution.sandbox import Sandbox
_test_sandbox = Sandbox(workspace_root=_TMP_DIR)

# Monkey-patch the module-level singleton so all executors use the test sandbox
import skills.execution.sandbox as _sb_mod
_sb_mod.sandbox = _test_sandbox

# Also patch inside each executor module (they import sandbox at module level)
import skills.executors.file_executor     as _fe_mod
import skills.executors.terminal_executor as _te_mod
import skills.executors.browser_executor  as _be_mod
import skills.executors.coding_executor   as _ce_mod
_fe_mod.sandbox = _test_sandbox
_te_mod.sandbox = _test_sandbox
_be_mod.sandbox = _test_sandbox
_ce_mod.sandbox = _test_sandbox

# ── Now import everything ──────────────────────────────────────────────────────
from rich.console import Console
from rich.rule import Rule

from skills.execution.execution_context import (
    ExecutionContext, ExecutionStatus, RiskLevel
)
from skills.execution.execution_history import ExecutionHistory
from skills.execution.permissions import PermissionManager, PermissionMode
from skills.execution.sandbox import SandboxViolation
from skills.execution.task_router import TaskRouter
from skills.executors.file_executor     import FileExecutor
from skills.executors.terminal_executor import TerminalExecutor, SAFE_COMMANDS
from skills.executors.browser_executor  import BrowserExecutor
from skills.executors.coding_executor   import CodingExecutor
from core.models import Goal

console = Console()

# ── Result tracking ────────────────────────────────────────────────────────────
_results = {"pass": 0, "fail": 0}


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        _results["pass"] += 1
        console.print(f"  [green]✓[/green]  {label}")
    else:
        _results["fail"] += 1
        msg = f"  [red]✗[/red]  {label}"
        if detail:
            msg += f"  [dim]({detail})[/dim]"
        console.print(msg)


def _ctx(executor: str, action: str, params: dict = None,
         risk: RiskLevel = RiskLevel.LOW) -> ExecutionContext:
    return ExecutionContext(
        task_id    = str(uuid.uuid4())[:8],
        executor   = executor,
        action     = action,
        params     = params or {},
        risk_level = risk,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Sandbox
# ─────────────────────────────────────────────────────────────────────────────

def test_sandbox():
    console.print("\n[bold cyan]── 1. Sandbox ──────────────────────────────────────────[/bold cyan]")

    # Valid path resolves inside workspace
    p = _test_sandbox.resolve("project/app.py")
    check("resolve() returns path inside workspace",
          str(p).startswith(_TMP_DIR))

    # Escape attempt raises SandboxViolation
    try:
        _test_sandbox.resolve("../../etc/passwd")
        check("escape attempt raises SandboxViolation", False, "no exception raised")
    except SandboxViolation:
        check("escape attempt raises SandboxViolation", True)

    # ensure_dir creates directory
    d = _test_sandbox.ensure_dir("sandbox_test_dir")
    check("ensure_dir creates directory", d.exists() and d.is_dir())

    # relative_display strips workspace prefix
    rel = _test_sandbox.relative_display(p)
    check("relative_display strips workspace prefix",
          rel == "project/app.py" or rel == r"project\app.py")


# ─────────────────────────────────────────────────────────────────────────────
# 2. FileExecutor
# ─────────────────────────────────────────────────────────────────────────────

def test_file_executor():
    console.print("\n[bold cyan]── 2. FileExecutor ─────────────────────────────────────[/bold cyan]")
    fe = FileExecutor()

    # create_file
    ctx = _ctx("file", "create_file", {"path": "fe_test/hello.txt", "content": "Hello JARVIS"})
    out = fe.execute(ctx)
    check("create_file returns success message", "Created" in out or "created" in out.lower())
    check("create_file actually creates the file",
          _test_sandbox.resolve("fe_test/hello.txt").exists())

    # create_file idempotent (already exists)
    ctx2 = _ctx("file", "create_file", {"path": "fe_test/hello.txt", "content": "new"})
    out2 = fe.execute(ctx2)
    check("create_file on existing file returns 'already exists'",
          "already exists" in out2.lower())

    # read_file
    ctx3 = _ctx("file", "read_file", {"path": "fe_test/hello.txt"})
    content = fe.execute(ctx3)
    check("read_file returns correct content", content == "Hello JARVIS")

    # write_file (overwrite)
    ctx4 = _ctx("file", "write_file", {"path": "fe_test/hello.txt", "content": "Updated"})
    fe.execute(ctx4)
    ctx5 = _ctx("file", "read_file", {"path": "fe_test/hello.txt"})
    check("write_file overwrites content", fe.execute(ctx5) == "Updated")

    # append_file
    ctx6 = _ctx("file", "append_file", {"path": "fe_test/log.txt", "content": "line1\n"})
    fe.execute(ctx6)
    ctx7 = _ctx("file", "append_file", {"path": "fe_test/log.txt", "content": "line2\n"})
    fe.execute(ctx7)
    ctx8 = _ctx("file", "read_file", {"path": "fe_test/log.txt"})
    check("append_file accumulates content", "line1" in fe.execute(ctx8))

    # list_dir
    ctx9 = _ctx("file", "list_dir", {"path": "fe_test"})
    listing = fe.execute(ctx9)
    check("list_dir returns file names", "hello.txt" in listing)

    # create_dir
    ctx10 = _ctx("file", "create_dir", {"path": "fe_test/subdir"})
    out10 = fe.execute(ctx10)
    check("create_dir creates directory",
          _test_sandbox.resolve("fe_test/subdir").is_dir())

    # rename_file
    ctx11 = _ctx("file", "rename_file",
                 {"path": "fe_test/log.txt", "new_path": "fe_test/renamed.txt"})
    fe.execute(ctx11)
    check("rename_file moves the file",
          _test_sandbox.resolve("fe_test/renamed.txt").exists())
    check("rename_file removes original",
          not _test_sandbox.resolve("fe_test/log.txt").exists())

    # delete_file
    ctx12 = _ctx("file", "delete_file", {"path": "fe_test/hello.txt"}, RiskLevel.MEDIUM)
    fe.execute(ctx12)
    check("delete_file removes the file",
          not _test_sandbox.resolve("fe_test/hello.txt").exists())

    # read_file on missing file raises
    try:
        fe.execute(_ctx("file", "read_file", {"path": "fe_test/missing.txt"}))
        check("read_file on missing file raises FileNotFoundError", False)
    except FileNotFoundError:
        check("read_file on missing file raises FileNotFoundError", True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. TerminalExecutor
# ─────────────────────────────────────────────────────────────────────────────

def test_terminal_executor():
    console.print("\n[bold cyan]── 3. TerminalExecutor ─────────────────────────────────[/bold cyan]")
    te = TerminalExecutor()

    # check_python
    ctx = _ctx("terminal", "check_python", {}, RiskLevel.SAFE)
    out = te.execute(ctx)
    check("check_python returns version string", "python" in out.lower() or "3." in out)

    # run_safe_command — echo
    ctx2 = _ctx("terminal", "run_safe_command", {"command": "echo hello_jarvis"})
    out2 = te.execute(ctx2)
    check("run_safe_command echo works", "hello_jarvis" in out2)

    # Blocked command raises ValueError
    try:
        te._validate_command("rm -rf /")
        check("blocked command raises ValueError", False)
    except ValueError:
        check("blocked command raises ValueError", True)

    # Non-whitelisted command raises ValueError
    try:
        te._validate_command("curl https://example.com")
        check("non-whitelisted command raises ValueError", False)
    except ValueError:
        check("non-whitelisted command raises ValueError", True)

    # Whitelist check
    check("'python' is in SAFE_COMMANDS", "python" in SAFE_COMMANDS)
    check("'pip' is in SAFE_COMMANDS",    "pip"    in SAFE_COMMANDS)
    check("'pytest' is in SAFE_COMMANDS", "pytest" in SAFE_COMMANDS)

    # Package name validation
    check("valid package name accepted",   te._is_safe_package_name("flask>=3.0.0"))
    check("invalid package name rejected", not te._is_safe_package_name("flask; rm -rf /"))


# ─────────────────────────────────────────────────────────────────────────────
# 4. BrowserExecutor
# ─────────────────────────────────────────────────────────────────────────────

def test_browser_executor():
    console.print("\n[bold cyan]── 4. BrowserExecutor ──────────────────────────────────[/bold cyan]")
    be = BrowserExecutor()

    # URL validation
    try:
        be._validate_url("")
        check("empty URL raises ValueError", False)
    except ValueError:
        check("empty URL raises ValueError", True)

    try:
        be._validate_url("ftp://bad.com")
        check("ftp:// URL raises ValueError", False)
    except ValueError:
        check("ftp:// URL raises ValueError", True)

    be._validate_url("https://example.com")
    check("https:// URL passes validation", True)

    # Supported actions declared
    check("open_url in SUPPORTED_ACTIONS",   "open_url"      in be.SUPPORTED_ACTIONS)
    check("search in SUPPORTED_ACTIONS",     "search"        in be.SUPPORTED_ACTIONS)
    check("fetch_page in SUPPORTED_ACTIONS", "fetch_page"    in be.SUPPORTED_ACTIONS)

    # Unsupported action raises ValueError
    try:
        be.execute(_ctx("browser", "click_button", {}))
        check("unsupported action raises ValueError", False)
    except ValueError:
        check("unsupported action raises ValueError", True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. CodingExecutor
# ─────────────────────────────────────────────────────────────────────────────

def test_coding_executor():
    console.print("\n[bold cyan]── 5. CodingExecutor ───────────────────────────────────[/bold cyan]")
    ce = CodingExecutor()

    # generate_project_structure (generic)
    ctx = _ctx("coding", "generate_project_structure", {
        "project_name": "test_project",
        "goal":         "Build a Python tool",
        "requirements": ["cli", "logging"],
    })
    out = ce.execute(ctx)
    check("generate_project_structure returns success",
          "test_project" in out or "created" in out.lower())
    check("project folder created",
          _test_sandbox.resolve("test_project").is_dir())
    check("tests/ subfolder created",
          _test_sandbox.resolve("test_project/tests").is_dir())

    # write_starter_files
    ctx2 = _ctx("coding", "write_starter_files", {
        "project_name": "test_project",
        "goal":         "Build a Python tool",
        "requirements": [],
    })
    ce.execute(ctx2)
    check(".gitignore created",
          _test_sandbox.resolve("test_project/.gitignore").exists())
    check("requirements.txt created",
          _test_sandbox.resolve("test_project/requirements.txt").exists())

    # generate_flask_project
    ctx3 = _ctx("coding", "generate_flask_project", {
        "project_name": "flask_test_api",
        "goal":         "Create Flask REST API",
        "requirements": ["authentication", "database"],
    })
    ce.execute(ctx3)
    check("Flask app.py created",
          _test_sandbox.resolve("flask_test_api/app.py").exists())
    check("Flask requirements.txt created",
          _test_sandbox.resolve("flask_test_api/requirements.txt").exists())
    check("Flask README.md created",
          _test_sandbox.resolve("flask_test_api/README.md").exists())

    # Flask app.py contains Flask import
    app_content = _test_sandbox.resolve("flask_test_api/app.py").read_text()
    check("Flask app.py contains Flask import", "from flask import" in app_content)

    # verify_syntax on valid file
    ctx4 = _ctx("coding", "verify_syntax", {"script_path": "flask_test_api/app.py"})
    out4 = ce.execute(ctx4)
    check("verify_syntax passes on valid Flask app", "Syntax OK" in out4)


# ─────────────────────────────────────────────────────────────────────────────
# 6. PermissionManager
# ─────────────────────────────────────────────────────────────────────────────

def test_permission_manager():
    console.print("\n[bold cyan]── 6. PermissionManager ────────────────────────────────[/bold cyan]")
    pm = PermissionManager(auto_approve_safe=True)

    # SAFE risk → auto-approved
    ctx_safe = _ctx("file", "read_file", {}, RiskLevel.SAFE)
    approved = pm.request(ctx_safe)
    check("SAFE risk auto-approved", approved)
    check("SAFE ctx.approved_by == 'auto'", ctx_safe.approved_by == "auto")

    # LOW risk → auto-approved
    ctx_low = _ctx("file", "create_file", {}, RiskLevel.LOW)
    approved_low = pm.request(ctx_low)
    check("LOW risk auto-approved", approved_low)

    # CRITICAL risk → always denied
    ctx_crit = _ctx("terminal", "run_safe_command", {}, RiskLevel.CRITICAL)
    denied = pm.request(ctx_crit)
    check("CRITICAL risk denied", not denied)
    check("CRITICAL ctx.status == DENIED",
          ctx_crit.status == ExecutionStatus.DENIED)

    # Blocked command pattern → denied
    ctx_blocked = _ctx("terminal", "run_safe_command",
                       {"command": "rm -rf /"}, RiskLevel.MEDIUM)
    denied2 = pm.request(ctx_blocked)
    check("blocked command pattern denied", not denied2)

    # Session override: force DENY on a normally-allowed action
    pm.set_override("file", "create_file", PermissionMode.DENY)
    ctx_override = _ctx("file", "create_file", {}, RiskLevel.LOW)
    denied3 = pm.request(ctx_override)
    check("session override DENY works", not denied3)


# ─────────────────────────────────────────────────────────────────────────────
# 7. ExecutionContext lifecycle
# ─────────────────────────────────────────────────────────────────────────────

def test_execution_context():
    console.print("\n[bold cyan]── 7. ExecutionContext Lifecycle ───────────────────────[/bold cyan]")

    ctx = ExecutionContext(
        task_id    = "test-task-001",
        executor   = "file",
        action     = "create_file",
        params     = {"path": "x.txt"},
        risk_level = RiskLevel.LOW,
    )
    check("initial status is PENDING", ctx.status == ExecutionStatus.PENDING)

    ctx.mark_running()
    check("mark_running sets RUNNING", ctx.status == ExecutionStatus.RUNNING)
    check("mark_running sets started_at", ctx.started_at is not None)

    ctx.mark_success("file created")
    check("mark_success sets SUCCESS", ctx.status == ExecutionStatus.SUCCESS)
    check("mark_success sets output", ctx.output == "file created")
    check("mark_success sets duration_ms", ctx.duration_ms is not None)

    ctx2 = ExecutionContext(task_id="t2", executor="terminal",
                            action="run", params={})
    ctx2.mark_running()
    ctx2.mark_failed("command not found")
    check("mark_failed sets FAILED", ctx2.status == ExecutionStatus.FAILED)
    check("mark_failed sets error", ctx2.error == "command not found")

    ctx3 = ExecutionContext(task_id="t3", executor="browser",
                            action="open_url", params={})
    ctx3.mark_denied()
    check("mark_denied sets DENIED", ctx3.status == ExecutionStatus.DENIED)

    # to_dict serialisation
    d = ctx.to_dict()
    check("to_dict contains task_id",  "task_id"  in d)
    check("to_dict contains executor", "executor" in d)
    check("to_dict contains status",   d["status"] == "success")


# ─────────────────────────────────────────────────────────────────────────────
# 8. ExecutionHistory
# ─────────────────────────────────────────────────────────────────────────────

def test_execution_history():
    console.print("\n[bold cyan]── 8. ExecutionHistory ─────────────────────────────────[/bold cyan]")

    import tempfile
    tmp = tempfile.mkdtemp(prefix="jarvis_hist_test_")
    hist = ExecutionHistory(log_dir=tmp, buffer_size=50)

    # Record a success
    ctx_ok = ExecutionContext(task_id="hist-001", executor="file",
                              action="create_file", params={})
    ctx_ok.mark_running()
    ctx_ok.mark_success("done")
    hist.record(ctx_ok)

    # Record a failure
    ctx_fail = ExecutionContext(task_id="hist-001", executor="terminal",
                                action="run_safe_command", params={})
    ctx_fail.mark_running()
    ctx_fail.mark_failed("error")
    hist.record(ctx_fail)

    check("get_recent returns 2 items", len(hist.get_recent(10)) == 2)
    check("get_by_task filters by task_id",
          len(hist.get_by_task("hist-001")) == 2)
    check("get_failed returns 1 item", len(hist.get_failed()) == 1)
    check("get_by_executor filters correctly",
          len(hist.get_by_executor("file")) == 1)

    summary = hist.summary()
    check("summary total == 2",   summary["total"]   == 2)
    check("summary success == 1", summary["success"] == 1)
    check("summary failed == 1",  summary["failed"]  == 1)

    # File was written
    from pathlib import Path
    from datetime import datetime
    log_file = Path(tmp) / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    check("JSONL log file created", log_file.exists())
    check("JSONL log has 2 lines",  len(log_file.read_text().strip().splitlines()) == 2)


# ─────────────────────────────────────────────────────────────────────────────
# 9. TaskRouter
# ─────────────────────────────────────────────────────────────────────────────

def test_task_router():
    console.print("\n[bold cyan]── 9. TaskRouter ───────────────────────────────────────[/bold cyan]")
    router = TaskRouter()

    def _goal(category: str, text: str = "test goal") -> Goal:
        return Goal(goal=text, category=category, confidence=85.0)

    # software_development → coding executor steps
    steps = router.route(_goal("software_development", "Build Flask API"))
    check("software_development generates steps", len(steps) > 0)
    executors = {s["executor"] for s in steps}
    check("software_development uses coding executor", "coding" in executors)

    # design → file + browser steps
    steps_d = router.route(_goal("design", "Create poster"))
    check("design generates steps", len(steps_d) > 0)
    executors_d = {s["executor"] for s in steps_d}
    check("design uses file executor",    "file"    in executors_d)
    check("design uses browser executor", "browser" in executors_d)

    # research → browser + file
    steps_r = router.route(_goal("research", "Research AI models"))
    check("research generates steps", len(steps_r) > 0)

    # system_operations → terminal + file
    steps_s = router.route(_goal("system_operations", "Clean temporary files"))
    check("system_operations generates steps", len(steps_s) > 0)
    executors_s = {s["executor"] for s in steps_s}
    check("system_operations uses terminal executor", "terminal" in executors_s)

    # Each step has required keys
    for step in steps:
        check(f"step has 'executor' key",    "executor"    in step)
        check(f"step has 'action' key",      "action"      in step)
        check(f"step has 'risk_level' key",  "risk_level"  in step)


# ─────────────────────────────────────────────────────────────────────────────
# 10. ExecutionManager (auto-approve mode)
# ─────────────────────────────────────────────────────────────────────────────

def test_execution_manager():
    console.print("\n[bold cyan]── 10. ExecutionManager (auto-approve) ─────────────────[/bold cyan]")

    from skills.execution.manager import ExecutionManager
    from skills.execution.permissions import PermissionManager, PermissionMode

    # Build a manager with auto-approve for all risk levels
    mgr = ExecutionManager()
    # Force all MEDIUM actions to auto-approve for testing
    mgr._executors["file"]._test_mode = True

    # Override permission manager to auto-approve everything
    auto_pm = PermissionManager(auto_approve_safe=True)
    auto_pm.set_override("browser", "open_url",  PermissionMode.ALLOW)
    auto_pm.set_override("browser", "search",    PermissionMode.ALLOW)
    auto_pm.set_override("terminal", "run_safe_command", PermissionMode.ALLOW)
    auto_pm.set_override("terminal", "verify_syntax",    PermissionMode.ALLOW)
    auto_pm.set_override("coding",  "generate_project_structure", PermissionMode.ALLOW)
    auto_pm.set_override("coding",  "write_starter_files",        PermissionMode.ALLOW)

    import skills.execution.manager as _mgr_mod
    original_pm = _mgr_mod.permission_manager
    _mgr_mod.permission_manager = auto_pm

    try:
        # Test software_development execution
        goal = Goal(
            goal="Build Flask API project",
            category="software_development",
            confidence=88.0,
            requirements=["authentication", "REST API"],
        )
        result = mgr.execute(goal)
        check("software_development execution completes", result is not None)
        check("software_development has contexts", len(result.contexts) > 0)
        check("software_development task_id set", bool(result.task_id))

        # Test design execution
        goal_d = Goal(
            goal="Create poster",
            category="design",
            confidence=90.0,
            requirements=["poster"],
        )
        result_d = mgr.execute(goal_d)
        check("design execution completes", result_d is not None)

        # Test that denied steps don't crash the system
        deny_pm = PermissionManager(auto_approve_safe=True)
        deny_pm.set_override("browser", "open_url", PermissionMode.DENY)
        _mgr_mod.permission_manager = deny_pm

        result_denied = mgr.execute(goal_d)
        check("denied step doesn't crash system", result_denied is not None)
        denied_count = sum(
            1 for c in result_denied.contexts
            if c.status == ExecutionStatus.DENIED
        )
        check("denied step recorded correctly", denied_count >= 1)

    finally:
        _mgr_mod.permission_manager = original_pm


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_sandbox()
    test_file_executor()
    test_terminal_executor()
    test_browser_executor()
    test_coding_executor()
    test_permission_manager()
    test_execution_context()
    test_execution_history()
    test_task_router()
    test_execution_manager()

    total = _results["pass"] + _results["fail"]
    console.print(f"\n{'═' * 60}")
    console.print(
        f"  Results: [green]{_results['pass']}[/green]/{total} passed  "
        f"([red]{_results['fail']}[/red] failed)"
    )
    console.print(f"{'═' * 60}\n")

    # Cleanup temp workspace
    import shutil
    shutil.rmtree(_TMP_DIR, ignore_errors=True)

    sys.exit(0 if _results["fail"] == 0 else 1)
