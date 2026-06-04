"""
test_orchestration.py
=====================
Automated test suite for JARVIS Milestone 3 — Multi-Skill Orchestration.

Covers
------
1.  SharedContext — artifact registration, key-value store, messaging
2.  DependencyManager — topological sort, cycle detection, blocked steps
3.  WorkflowState — lifecycle, step tracking, serialisation
4.  WorkflowRegistry — template resolution per category
5.  WorkflowValidator — param checks, executor checks, dependency checks
6.  WorkflowMemory — save, query, summary
7.  Full Flask API pipeline — end-to-end with auto-approve
8.  Full Portfolio Website pipeline — multi-executor collaboration
9.  Full Research pipeline — browser → file flow
10. Dependency ordering — steps execute in correct order
11. Failure recovery — blocked steps don't crash workflow
12. Shared context cross-executor messaging
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Isolate sandbox ────────────────────────────────────────────────────────────
_TMP_DIR = tempfile.mkdtemp(prefix="jarvis_orch_test_")
from skills.execution.sandbox import Sandbox
_test_sandbox = Sandbox(workspace_root=_TMP_DIR)
import skills.execution.sandbox as _sb_mod
_sb_mod.sandbox = _test_sandbox
import skills.executors.file_executor     as _fe_mod
import skills.executors.terminal_executor as _te_mod
import skills.executors.browser_executor  as _be_mod
import skills.executors.coding_executor   as _ce_mod
_fe_mod.sandbox = _test_sandbox
_te_mod.sandbox = _test_sandbox
_be_mod.sandbox = _test_sandbox
_ce_mod.sandbox = _test_sandbox

from rich.console import Console
from orchestration.context_manager import SharedContext
from orchestration.dependency_manager import DependencyManager, DependencyError
from orchestration.workflow_memory import WorkflowMemory
from orchestration.workflow_registry import WorkflowRegistry, workflow_registry
from orchestration.workflow_state import WorkflowState, WorkflowStep, WorkflowStatus, StepStatus
from orchestration.workflow_validator import WorkflowValidator
from orchestration.workflow_orchestrator import WorkflowOrchestrator
from skills.execution.execution_context import RiskLevel
from skills.execution.permissions import PermissionManager, PermissionMode
from core.models import Goal

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


def _goal(text: str, category: str = "software_development",
          reqs: list = None) -> Goal:
    return Goal(goal=text, category=category, confidence=88.0,
                requirements=reqs or [])


def _step(name: str, executor: str = "file", action: str = "create_file",
          params: dict = None, depends_on: list = None,
          stage: str = "main") -> WorkflowStep:
    return WorkflowStep(
        name=name, executor=executor, action=action,
        params=params or {"path": f"test_{name}.txt", "content": "x"},
        depends_on=depends_on or [], stage=stage,
        risk_level=RiskLevel.LOW.value,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. SharedContext
# ─────────────────────────────────────────────────────────────────────────────

def test_shared_context():
    console.print("\n[bold cyan]── 1. SharedContext ────────────────────────────────────[/bold cyan]")
    ctx = SharedContext("wf-001", "t-001", "Build Flask API", "software_development")

    ctx.add_file("project/app.py")
    ctx.add_file("project/app.py")   # duplicate — should not double-add
    check("add_file deduplicates", len(ctx.generated_files) == 1)
    check("add_file stores path", "project/app.py" in ctx.generated_files)

    ctx.add_dir("project/tests")
    check("add_dir stores path", "project/tests" in ctx.created_dirs)

    ctx.add_package("flask")
    ctx.add_package("flask")   # duplicate
    check("add_package deduplicates", len(ctx.installed_packages) == 1)

    ctx.add_browser_result("https://example.com", "some content here")
    check("add_browser_result stores entry", len(ctx.browser_results) == 1)

    ctx.set("project_name", "my_api")
    check("set/get round-trip", ctx.get("project_name") == "my_api")
    check("has() returns True for set key", ctx.has("project_name"))
    check("has() returns False for missing key", not ctx.has("nonexistent"))
    check("get() returns default for missing key", ctx.get("missing", 42) == 42)

    ctx.post_message("browser", "coding", "template_url", "https://t.co/x")
    msgs = ctx.read_messages("coding")
    check("post_message / read_messages works", len(msgs) == 1)
    check("message key correct", msgs[0]["key"] == "template_url")

    val = ctx.get_message_value("coding", "template_url")
    check("get_message_value returns value", val == "https://t.co/x")
    check("get_message_value returns default for missing", 
          ctx.get_message_value("coding", "nonexistent", "default") == "default")

    ctx.add_error("step1", "something failed")
    check("add_error stores entry", len(ctx.errors) == 1)

    d = ctx.to_dict()
    check("to_dict has workflow_id", d["workflow_id"] == "wf-001")
    check("to_dict has generated_files", "generated_files" in d)
    check("to_dict has store", "store" in d)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DependencyManager
# ─────────────────────────────────────────────────────────────────────────────

def test_dependency_manager():
    console.print("\n[bold cyan]── 2. DependencyManager ────────────────────────────────[/bold cyan]")

    # Linear chain: s1 → s2 → s3
    s1 = _step("s1")
    s2 = _step("s2", depends_on=[s1.step_id])
    s3 = _step("s3", depends_on=[s2.step_id])
    order = DependencyManager.resolve_order([s3, s1, s2])  # intentionally shuffled
    check("linear chain resolves in order",
          [s.name for s in order] == ["s1", "s2", "s3"])

    # Diamond: s1 → s2, s1 → s3, s2+s3 → s4
    a = _step("a")
    b = _step("b", depends_on=[a.step_id])
    c = _step("c", depends_on=[a.step_id])
    d = _step("d", depends_on=[b.step_id, c.step_id])
    order2 = DependencyManager.resolve_order([d, b, c, a])
    check("diamond: 'a' is first", order2[0].name == "a")
    check("diamond: 'd' is last",  order2[-1].name == "d")
    check("diamond: all 4 steps present", len(order2) == 4)

    # Cycle detection
    x = _step("x")
    y = _step("y", depends_on=[x.step_id])
    x.depends_on = [y.step_id]   # create cycle
    try:
        DependencyManager.resolve_order([x, y])
        check("cycle detection raises DependencyError", False)
    except DependencyError:
        check("cycle detection raises DependencyError", True)

    # Missing dependency reference
    z = _step("z", depends_on=["nonexistent-id"])
    try:
        DependencyManager.resolve_order([z])
        check("missing dep raises DependencyError", False)
    except DependencyError:
        check("missing dep raises DependencyError", True)

    # get_ready_steps
    p = _step("p")
    q = _step("q", depends_on=[p.step_id])
    ready = DependencyManager.get_ready_steps([p, q], completed_ids=set())
    check("get_ready_steps: only p is ready (q has unmet dep)", 
          len(ready) == 1 and ready[0].name == "p")

    # Mark p as success so it's no longer PENDING, then q should be ready
    p.status = StepStatus.SUCCESS
    ready2 = DependencyManager.get_ready_steps([p, q], completed_ids={p.step_id})
    check("get_ready_steps: q ready after p completes",
          len(ready2) == 1 and ready2[0].name == "q")

    # get_blocked_steps
    f = _step("f")
    g = _step("g", depends_on=[f.step_id])
    blocked = DependencyManager.get_blocked_steps([f, g], failed_or_denied_ids={f.step_id})
    check("get_blocked_steps: g blocked when f fails", 
          len(blocked) == 1 and blocked[0].name == "g")


# ─────────────────────────────────────────────────────────────────────────────
# 3. WorkflowState
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_state():
    console.print("\n[bold cyan]── 3. WorkflowState ────────────────────────────────────[/bold cyan]")

    s1 = _step("step1"); s1.mark_success("ok")
    s2 = _step("step2"); s2.mark_failed("err")
    s3 = _step("step3"); s3.mark_denied()

    state = WorkflowState(
        workflow_id="wf-test", workflow_name="test_wf",
        goal_text="test goal", steps=[s1, s2, s3],
    )
    state.mark_running()
    check("mark_running sets RUNNING", state.status == WorkflowStatus.RUNNING)

    state.mark_finished()
    check("mark_finished sets PARTIALLY_COMPLETED",
          state.status == WorkflowStatus.PARTIALLY_COMPLETED)
    check("success_steps count == 1", len(state.success_steps) == 1)
    check("failed_steps count == 1",  len(state.failed_steps)  == 1)
    check("denied_steps count == 1",  len(state.denied_steps)  == 1)
    check("duration_ms is set", state.duration_ms is not None)

    # All success → COMPLETED
    s4 = _step("s4"); s4.mark_success("ok")
    s5 = _step("s5"); s5.mark_success("ok")
    state2 = WorkflowState("wf2", "wf2", "g", steps=[s4, s5])
    state2.mark_running(); state2.mark_finished()
    check("all success → COMPLETED", state2.status == WorkflowStatus.COMPLETED)

    # Serialisation
    d = state.to_dict()
    check("to_dict has workflow_id",   d["workflow_id"] == "wf-test")
    check("to_dict has steps list",    isinstance(d["steps"], list))
    check("to_dict has summary",       "summary" in d)
    check("summary total == 3",        d["summary"]["total"] == 3)

    # get_step
    found = state.get_step(s1.step_id)
    check("get_step returns correct step", found is s1)
    check("get_step returns None for missing", state.get_step("bad-id") is None)

    # stages
    sa = _step("sa", stage="setup")
    sb = _step("sb", stage="build")
    sc = _step("sc", stage="setup")
    state3 = WorkflowState("wf3", "wf3", "g", steps=[sa, sb, sc])
    check("stages deduplicates", state3.stages == ["setup", "build"])


# ─────────────────────────────────────────────────────────────────────────────
# 4. WorkflowRegistry
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_registry():
    console.print("\n[bold cyan]── 4. WorkflowRegistry ─────────────────────────────────[/bold cyan]")
    reg = WorkflowRegistry()

    # software_development → flask_api template
    name, steps = reg.resolve(_goal("Build Flask API", "software_development"))
    check("software_development resolves to flask_api", name == "flask_api")
    check("flask_api has steps", len(steps) > 0)
    executors = {s.executor for s in steps}
    check("flask_api uses coding executor", "coding" in executors)
    check("flask_api uses file executor",   "file"   in executors)

    # design → design_brief template
    name2, steps2 = reg.resolve(_goal("Create poster", "design"))
    check("design resolves to design_brief", name2 == "design_brief")
    check("design_brief uses browser executor", 
          any(s.executor == "browser" for s in steps2))

    # research → research_pipeline
    name3, steps3 = reg.resolve(_goal("Research AI models", "research"))
    check("research resolves to research_pipeline", name3 == "research_pipeline")

    # portfolio keyword override
    name4, steps4 = reg.resolve(_goal("Build portfolio website", "software_development"))
    check("portfolio keyword → portfolio_website template", name4 == "portfolio_website")
    check("portfolio_website has browser step",
          any(s.executor == "browser" for s in steps4))

    # Direct template access
    steps5 = reg.get_template("python_script", _goal("Write a script"))
    check("get_template returns steps", len(steps5) > 0)

    # Unknown template raises KeyError
    try:
        reg.get_template("nonexistent_template", _goal("x"))
        check("unknown template raises KeyError", False)
    except KeyError:
        check("unknown template raises KeyError", True)

    # list_templates
    templates = reg.list_templates()
    check("list_templates returns list", isinstance(templates, list))
    check("flask_api in templates", "flask_api" in templates)
    check("portfolio_website in templates", "portfolio_website" in templates)


# ─────────────────────────────────────────────────────────────────────────────
# 5. WorkflowValidator
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_validator():
    console.print("\n[bold cyan]── 5. WorkflowValidator ────────────────────────────────[/bold cyan]")
    from skills.executors.file_executor     import FileExecutor
    from skills.executors.terminal_executor import TerminalExecutor
    from skills.executors.browser_executor  import BrowserExecutor
    from skills.executors.coding_executor   import CodingExecutor

    executors = {
        "file": FileExecutor(), "terminal": TerminalExecutor(),
        "browser": BrowserExecutor(), "coding": CodingExecutor(),
    }
    validator = WorkflowValidator(executors)

    # Valid steps
    s1 = _step("s1", "file", "create_file", {"path": "x.txt", "content": "y"})
    report = validator.validate([s1])
    check("valid step passes validation", report.is_valid)

    # Unknown executor
    bad_exec = _step("bad", "nonexistent_executor", "create_file", {"path": "x.txt"})
    report2 = validator.validate([bad_exec])
    check("unknown executor produces error", not report2.is_valid)

    # Unsupported action
    bad_action = _step("bad2", "file", "teleport_file", {"path": "x.txt"})
    report3 = validator.validate([bad_action])
    check("unsupported action produces error", not report3.is_valid)

    # Missing required param — create step directly with empty params
    from orchestration.workflow_state import WorkflowStep as WS
    missing_param = WS(name="bad3", executor="file", action="create_file",
                       params={}, risk_level=RiskLevel.LOW.value)
    report4 = validator.validate([missing_param])
    check("missing required param produces error", not report4.is_valid)

    # HIGH risk produces warning
    high_risk = WorkflowStep(
        name="install", executor="terminal", action="install_package",
        params={"package": "flask"}, risk_level=RiskLevel.HIGH.value,
    )
    report5 = validator.validate([high_risk])
    check("HIGH risk step produces warning", len(report5.warnings) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# 6. WorkflowMemory
# ─────────────────────────────────────────────────────────────────────────────

def test_workflow_memory():
    console.print("\n[bold cyan]── 6. WorkflowMemory ───────────────────────────────────[/bold cyan]")
    import tempfile
    tmp = tempfile.mkdtemp(prefix="jarvis_wfmem_")
    mem = WorkflowMemory(log_dir=tmp, buffer_size=50)

    def _state(wid, name, status):
        s = WorkflowState(workflow_id=wid, workflow_name=name, goal_text="test")
        s.status = status
        return s

    s1 = _state("w1", "flask_api", WorkflowStatus.COMPLETED)
    s2 = _state("w2", "research_pipeline", WorkflowStatus.FAILED)
    s3 = _state("w3", "flask_api", WorkflowStatus.PARTIALLY_COMPLETED)
    mem.save(s1); mem.save(s2); mem.save(s3)

    check("get_recent returns 3", len(mem.get_recent(10)) == 3)
    check("get_recent newest first", mem.get_recent(1)[0].workflow_id == "w3")
    check("get_by_id finds w2", mem.get_by_id("w2") is s2)
    check("get_by_id returns None for missing", mem.get_by_id("bad") is None)
    check("get_by_name finds flask_api", len(mem.get_by_name("flask_api")) == 2)
    check("get_failed returns 2", len(mem.get_failed()) == 2)
    check("get_completed returns 1", len(mem.get_completed()) == 1)

    summary = mem.summary()
    check("summary total == 3",     summary["total"]     == 3)
    check("summary completed == 1", summary["completed"] == 1)
    check("summary failed == 1",    summary["failed"]    == 1)
    check("summary partial == 1",   summary["partial"]   == 1)

    # JSONL file written
    from pathlib import Path
    from datetime import datetime
    log_file = Path(tmp) / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    check("JSONL log file created", log_file.exists())
    check("JSONL has 3 lines", len(log_file.read_text().strip().splitlines()) == 3)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build auto-approve orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def _auto_orchestrator() -> WorkflowOrchestrator:
    """Return an orchestrator with all permissions auto-approved."""
    import skills.execution.manager as _mgr_mod
    import orchestration.workflow_orchestrator as _orch_mod

    auto_pm = PermissionManager(auto_approve_safe=True)
    for executor in ("file", "coding", "terminal", "browser"):
        for action in (
            "create_file", "write_file", "append_file", "create_dir",
            "generate_project_structure", "write_starter_files",
            "generate_flask_project", "generate_python_script",
            "verify_syntax", "open_url", "search", "fetch_page",
            "run_safe_command", "check_python",
        ):
            auto_pm.set_override(executor, action, PermissionMode.ALLOW)

    _orch_mod.permission_manager = auto_pm
    orch = WorkflowOrchestrator()
    return orch


# ─────────────────────────────────────────────────────────────────────────────
# 7. Full Flask API pipeline
# ─────────────────────────────────────────────────────────────────────────────

def test_full_flask_pipeline():
    console.print("\n[bold cyan]── 7. Full Flask API Pipeline ──────────────────────────[/bold cyan]")
    orch   = _auto_orchestrator()
    goal   = _goal("Build Flask API project", "software_development",
                   reqs=["authentication", "REST API"])
    result = orch.run(goal)

    check("flask pipeline completes", result.state.status in (
        WorkflowStatus.COMPLETED, WorkflowStatus.PARTIALLY_COMPLETED))
    check("flask pipeline has contexts", len(result.state.steps) > 0)
    check("flask pipeline workflow_id set", bool(result.workflow_id))

    # Files created in workspace
    pname = "build_flask_api_project"
    check("app.py created",
          _test_sandbox.resolve(f"{pname}/app.py").exists())
    check("README.md created",
          _test_sandbox.resolve(f"{pname}/README.md").exists())

    # SharedContext populated
    check("shared context has generated files",
          len(result.context.generated_files) > 0 or
          len(result.context.created_dirs) > 0)

    # Success steps > 0
    check("at least 2 steps succeeded", len(result.state.success_steps) >= 2)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Full Portfolio Website pipeline
# ─────────────────────────────────────────────────────────────────────────────

def test_portfolio_pipeline():
    console.print("\n[bold cyan]── 8. Portfolio Website Pipeline ───────────────────────[/bold cyan]")
    orch   = _auto_orchestrator()
    goal   = _goal("Build portfolio website", "software_development",
                   reqs=["projects", "contact"])
    result = orch.run(goal)

    check("portfolio pipeline runs", result is not None)
    check("portfolio uses portfolio_website template",
          result.state.workflow_name == "portfolio_website")
    check("portfolio has 8 steps", len(result.state.steps) == 8)

    # Multi-executor collaboration
    executors_used = {s.executor for s in result.state.steps}
    check("portfolio uses browser executor", "browser" in executors_used)
    check("portfolio uses coding executor",  "coding"  in executors_used)
    check("portfolio uses file executor",    "file"    in executors_used)

    # Browser search result in shared context
    check("browser results captured in context",
          len(result.context.browser_results) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Research pipeline
# ─────────────────────────────────────────────────────────────────────────────

def test_research_pipeline():
    console.print("\n[bold cyan]── 9. Research Pipeline ────────────────────────────────[/bold cyan]")
    orch   = _auto_orchestrator()
    goal   = _goal("Research latest AI models", "research")
    result = orch.run(goal)

    check("research pipeline runs", result is not None)
    check("research uses research_pipeline template",
          result.state.workflow_name == "research_pipeline")

    # Notes file created
    pname = "research_latest_ai_models"
    notes = _test_sandbox.resolve(f"research/{pname}_notes.md")
    check("research notes file created", notes.exists())

    # Browser result in context
    check("browser search result in context",
          len(result.context.browser_results) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# 10. Dependency ordering
# ─────────────────────────────────────────────────────────────────────────────

def test_dependency_ordering():
    console.print("\n[bold cyan]── 10. Dependency Ordering ─────────────────────────────[/bold cyan]")
    execution_order = []

    # Build steps with explicit dependencies
    s1 = WorkflowStep(
        name="create_dir", executor="file", action="create_dir",
        params={"path": "dep_test/src"}, risk_level=RiskLevel.LOW.value,
        stage="setup",
    )
    s2 = WorkflowStep(
        name="create_file", executor="file", action="create_file",
        params={"path": "dep_test/src/main.py", "content": "# main"},
        risk_level=RiskLevel.LOW.value, stage="build",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="append_log", executor="file", action="append_file",
        params={"path": "dep_test/build.log", "content": "built\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
        depends_on=[s2.step_id],
    )

    # Resolve order (shuffled input)
    ordered = DependencyManager.resolve_order([s3, s1, s2])
    check("s1 executes first", ordered[0].name == "create_dir")
    check("s2 executes second", ordered[1].name == "create_file")
    check("s3 executes third", ordered[2].name == "append_log")

    # Run through orchestrator
    orch   = _auto_orchestrator()
    state  = WorkflowOrchestrator.__new__(WorkflowOrchestrator)
    state._executors = orch._executors

    import orchestration.workflow_orchestrator as _orch_mod
    shared = SharedContext("dep-test", "dep-test", "dep test", "software_development")
    wf_state = WorkflowState("dep-test", "dep_test", "dep test", steps=ordered)
    wf_state.mark_running()
    orch._execute_workflow(wf_state, shared)
    wf_state.mark_finished()

    check("all 3 dep steps succeeded",
          len(wf_state.success_steps) == 3,
          f"success={len(wf_state.success_steps)}")
    check("dep_test/src/main.py created",
          _test_sandbox.resolve("dep_test/src/main.py").exists())


# ─────────────────────────────────────────────────────────────────────────────
# 11. Failure recovery — blocked steps
# ─────────────────────────────────────────────────────────────────────────────

def test_failure_recovery():
    console.print("\n[bold cyan]── 11. Failure Recovery ────────────────────────────────[/bold cyan]")

    # s1 will fail (bad path escape attempt → sandbox violation)
    s1 = WorkflowStep(
        name="bad_step", executor="file", action="create_file",
        params={"path": "../../etc/passwd", "content": "x"},
        risk_level=RiskLevel.LOW.value, stage="setup",
    )
    s2 = WorkflowStep(
        name="dependent_step", executor="file", action="create_file",
        params={"path": "recovery_test/ok.txt", "content": "ok"},
        risk_level=RiskLevel.LOW.value, stage="build",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="independent_step", executor="file", action="create_file",
        params={"path": "recovery_test/independent.txt", "content": "independent"},
        risk_level=RiskLevel.LOW.value, stage="build",
    )

    orch = _auto_orchestrator()
    import orchestration.workflow_orchestrator as _orch_mod
    ordered = DependencyManager.resolve_order([s1, s2, s3])
    shared  = SharedContext("rec-test", "rec-test", "recovery test", "general")
    wf_state = WorkflowState("rec-test", "recovery", "recovery test", steps=ordered)
    wf_state.mark_running()
    orch._execute_workflow(wf_state, shared)
    wf_state.mark_finished()

    check("bad_step failed (sandbox violation)", s1.status == StepStatus.FAILED)
    check("dependent_step blocked (not failed)", s2.status == StepStatus.BLOCKED)
    check("independent_step succeeded", s3.status == StepStatus.SUCCESS)
    check("workflow does not crash", wf_state.status in (
        WorkflowStatus.PARTIALLY_COMPLETED, WorkflowStatus.FAILED))
    check("independent file created",
          _test_sandbox.resolve("recovery_test/independent.txt").exists())
    check("errors captured in context", len(shared.errors) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# 12. Cross-executor messaging
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_executor_messaging():
    console.print("\n[bold cyan]── 12. Cross-Executor Messaging ────────────────────────[/bold cyan]")
    ctx = SharedContext("msg-test", "msg-test", "messaging test", "software_development")

    # Simulate browser posting search results to coding
    ctx.post_message("browser", "coding", "search_results", "Flask tutorial found")
    ctx.post_message("browser", "coding", "template_url",   "https://example.com/flask")
    ctx.post_message("coding",  "file",   "project_name",   "my_project")

    # coding reads its messages
    coding_msgs = ctx.read_messages("coding")
    check("coding receives 2 messages", len(coding_msgs) == 2)

    # file reads its messages
    file_msgs = ctx.read_messages("file")
    check("file receives 1 message", len(file_msgs) == 1)

    # filter by key
    url_msgs = ctx.read_messages("coding", key="template_url")
    check("filter by key returns 1 message", len(url_msgs) == 1)
    check("message value correct", url_msgs[0]["value"] == "https://example.com/flask")

    # get_message_value convenience
    val = ctx.get_message_value("coding", "search_results")
    check("get_message_value returns latest", val == "Flask tutorial found")

    # Messages from different senders don't mix
    browser_to_file = ctx.read_messages("file")
    check("file only gets messages addressed to it", 
          all(m["to"] == "file" for m in browser_to_file))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_shared_context()
    test_dependency_manager()
    test_workflow_state()
    test_workflow_registry()
    test_workflow_validator()
    test_workflow_memory()
    test_full_flask_pipeline()
    test_portfolio_pipeline()
    test_research_pipeline()
    test_dependency_ordering()
    test_failure_recovery()
    test_cross_executor_messaging()

    total = _results["pass"] + _results["fail"]
    console.print(f"\n{'═' * 60}")
    console.print(
        f"  Results: [green]{_results['pass']}[/green]/{total} passed  "
        f"([red]{_results['fail']}[/red] failed)"
    )
    console.print(f"{'═' * 60}\n")

    import shutil
    shutil.rmtree(_TMP_DIR, ignore_errors=True)
    sys.exit(0 if _results["fail"] == 0 else 1)
