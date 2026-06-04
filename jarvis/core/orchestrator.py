"""
workflow_orchestrator.py
========================
WorkflowOrchestrator — Milestone 3 centrepiece.

Pipeline
--------
  Goal
    ↓  WorkflowRegistry.resolve()       → workflow_name, [WorkflowStep, ...]
    ↓  WorkflowValidator.validate()     → ValidationReport
    ↓  DependencyManager.resolve_order()→ topologically-sorted steps
    ↓  [for each step]
         PermissionManager.request()    → approved / denied
         Executor.execute(ctx)          → output string
         SharedContext.add_*(output)    → cross-executor data sharing
         WorkflowState.mark_*()         → lifecycle tracking
    ↓  WorkflowMemory.save(state)       → persistence
    ↓  Console UX                       → rich output

Key design principles
---------------------
- Steps execute in dependency order, never out of order.
- A failed step marks its dependents as BLOCKED (not FAILED).
- A denied step does NOT block dependents — the workflow continues.
- SharedContext is passed to every executor so outputs flow downstream.
- The orchestrator never crashes — all exceptions are caught per-step.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Set

from jarvis.core.models import Goal
from jarvis.core.context_manager import SharedContext
from jarvis.core.dependency_manager import DependencyManager, DependencyError
from jarvis.core.workflow_memory import workflow_memory
from jarvis.core.workflow_registry import workflow_registry
from jarvis.core.workflow_state import (
    WorkflowState, WorkflowStep, WorkflowStatus, StepStatus
)
from jarvis.memory.workflow_checkpoint import workflow_checkpoint
from jarvis.core.verifier import WorkflowValidator
from jarvis.execution.execution_context import ExecutionContext, RiskLevel
from jarvis.execution.execution_history import execution_history
from jarvis.execution.permissions import permission_manager
from jarvis.execution.sandbox import sandbox

logger = logging.getLogger(__name__)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.rule import Rule
    from rich import box
    _console = Console()
    _RICH = True
except ImportError:
    _RICH = False
    _console = None  # type: ignore

# ── Risk level string → enum ───────────────────────────────────────────────────
_RISK_MAP = {
    "safe":     RiskLevel.SAFE,
    "low":      RiskLevel.LOW,
    "medium":   RiskLevel.MEDIUM,
    "high":     RiskLevel.HIGH,
    "critical": RiskLevel.CRITICAL,
}


class WorkflowResult:
    """Aggregated result returned to the caller after a workflow run."""

    def __init__(self, state: WorkflowState, context: SharedContext):
        self.state:   WorkflowState = state
        self.context: SharedContext = context

    @property
    def succeeded(self) -> bool:
        return self.state.status == WorkflowStatus.COMPLETED

    @property
    def workflow_id(self) -> str:
        return self.state.workflow_id

    def __repr__(self) -> str:
        return (
            f"WorkflowResult(name={self.state.workflow_name!r}, "
            f"status={self.state.status.value}, "
            f"success={len(self.state.success_steps)}, "
            f"failed={len(self.state.failed_steps)})"
        )


class WorkflowOrchestrator:
    """
    Central multi-skill workflow orchestrator.

    Usage
    -----
    result = orchestrator.run(goal)
    """

    def __init__(self):
        self._executors: Dict[str, Any] = {}
        self._register_executors()

    # ── Executor registry ──────────────────────────────────────────────────────

    def _register_executors(self) -> None:
        from jarvis.skills.executors.file_executor     import FileExecutor
        from jarvis.skills.executors.terminal_executor import TerminalExecutor
        from jarvis.skills.executors.browser_executor  import BrowserExecutor
        from jarvis.skills.executors.coding_executor   import CodingExecutor
        from jarvis.skills.executors.voice_executor    import VoiceExecutor

        self._executors = {
            "file":     FileExecutor(),
            "terminal": TerminalExecutor(),
            "browser":  BrowserExecutor(),
            "coding":   CodingExecutor(),
            "voice":    VoiceExecutor(),
        }
        logger.info(f"WorkflowOrchestrator: registered {list(self._executors.keys())}")

    def register_executor(self, name: str, executor: Any) -> None:
        self._executors[name] = executor

    # ── Main entry point ───────────────────────────────────────────────────────

    def run(self, goal: Goal) -> WorkflowResult:
        workflow_id = str(uuid.uuid4())[:12]

        # 1. Resolve workflow template
        workflow_name, steps = workflow_registry.resolve(goal)
        logger.info(
            f"WorkflowOrchestrator: resolved template={workflow_name!r} "
            f"with {len(steps)} steps"
        )

        # 2. Validate
        validator = WorkflowValidator(self._executors)
        report    = validator.validate(steps)
        if not report.is_valid:
            self._print_validation_failure(report)
            state = WorkflowState(
                workflow_id=workflow_id, workflow_name=workflow_name,
                goal_text=goal.goal, steps=steps,
                status=WorkflowStatus.FAILED,
                error=f"Validation failed: {report.errors}",
            )
            workflow_memory.save(state)
            ctx = SharedContext(workflow_id, workflow_id, goal.goal, goal.category)
            return WorkflowResult(state, ctx)

        # 3. Topological sort
        try:
            ordered_steps = DependencyManager.resolve_order(steps)
        except DependencyError as exc:
            logger.error(f"Dependency resolution failed: {exc}")
            state = WorkflowState(
                workflow_id=workflow_id, workflow_name=workflow_name,
                goal_text=goal.goal, steps=steps,
                status=WorkflowStatus.FAILED, error=str(exc),
            )
            workflow_memory.save(state)
            ctx = SharedContext(workflow_id, workflow_id, goal.goal, goal.category)
            return WorkflowResult(state, ctx)

        # 4. Build state + shared context
        state = WorkflowState(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            goal_text=goal.goal,
            steps=ordered_steps,
        )
        shared_ctx = SharedContext(
            workflow_id=workflow_id,
            task_id=workflow_id,
            goal=goal.goal,
            category=goal.category,
        )

        # 5. Print header
        self._print_workflow_header(goal, workflow_name, workflow_id, ordered_steps, report)

        # 6. Execute
        state.mark_running()
        self._execute_workflow(state, shared_ctx)
        state.mark_finished()

        # 7. Delete checkpoint (completed successfully)
        workflow_checkpoint.delete_checkpoint(state.workflow_id)

        # 8. Persist
        workflow_memory.save(state)

        # 8. Print summary
        self._print_workflow_summary(state, shared_ctx)

        return WorkflowResult(state, shared_ctx)

    # ── Execution loop ─────────────────────────────────────────────────────────

    def _execute_workflow(
        self, state: WorkflowState, shared_ctx: SharedContext
    ) -> None:
        completed_ids:        Set[str] = set()
        failed_or_denied_ids: Set[str] = set()
        total = len(state.steps)

        for idx, step in enumerate(state.steps, start=1):
            # Check if this step is blocked by a failed dependency
            if any(dep in failed_or_denied_ids for dep in step.depends_on):
                reason = (
                    f"Blocked: dependency "
                    f"{[d for d in step.depends_on if d in failed_or_denied_ids]} failed"
                )
                step.mark_blocked(reason)
                shared_ctx.add_error(step.name, reason)
                self._print_step_result(step, idx, total)
                continue

            # Print step header
            self._print_step_header(step, idx, total)

            # Build ExecutionContext
            ctx = ExecutionContext(
                task_id    = state.workflow_id,
                executor   = step.executor,
                action     = step.action,
                params     = step.params,
                risk_level = _RISK_MAP.get(step.risk_level, RiskLevel.LOW),
            )
            step.executor_ctx = ctx

            # Permission gate
            approved = permission_manager.request(ctx)
            if not approved:
                step.mark_denied()
                shared_ctx.add_error(step.name, "Denied by permission manager")
                execution_history.record(ctx)
                self._print_step_result(step, idx, total)
                # Denied steps do NOT block dependents
                completed_ids.add(step.step_id)
                continue

            # Execute
            step.mark_running()
            executor = self._executors.get(step.executor)
            if executor is None:
                err = f"Unknown executor: {step.executor!r}"
                step.mark_failed(err)
                shared_ctx.add_error(step.name, err)
                failed_or_denied_ids.add(step.step_id)
                execution_history.record(ctx)
                self._print_step_result(step, idx, total)
                continue

            ctx.mark_running()
            try:
                output = executor.execute(ctx)
                ctx.mark_success(output or "")
                step.mark_success(output or "")

                # ── Update shared context from output ─────────────────────────
                self._update_shared_context(step, output or "", shared_ctx)

                completed_ids.add(step.step_id)

            except Exception as exc:
                err = str(exc)
                logger.error(
                    f"[{step.executor}.{step.action}] failed: {err}", exc_info=True
                )
                ctx.mark_failed(err)
                step.mark_failed(err)
                shared_ctx.add_error(step.name, err)
                failed_or_denied_ids.add(step.step_id)

            execution_history.record(ctx)
            self._print_step_result(step, idx, total)
            # Save checkpoint after each step
            workflow_checkpoint.save_checkpoint(state)

    # ── Shared context updater ─────────────────────────────────────────────────

    @staticmethod
    def _update_shared_context(
        step: WorkflowStep, output: str, ctx: SharedContext
    ) -> None:
        """
        After a successful step, push relevant data into SharedContext
        so downstream executors can read it.
        """
        ctx.add_output(step.name, output)

        # File executor outputs
        if step.executor == "file":
            if step.action in ("create_file", "write_file"):
                path = step.params.get("path", "")
                if path:
                    ctx.add_file(path)
            elif step.action == "create_dir":
                path = step.params.get("path", "")
                if path:
                    ctx.add_dir(path)

        # Coding executor outputs
        elif step.executor == "coding":
            if step.action in ("generate_project_structure", "generate_flask_project"):
                pname = step.params.get("project_name", "")
                if pname:
                    ctx.add_dir(pname)
                    ctx.set("project_name", pname)
                    # Post message for downstream executors
                    ctx.post_message(
                        from_executor="coding",
                        to_executor="terminal",
                        key="project_name",
                        value=pname,
                    )

        # Terminal executor outputs
        elif step.executor == "terminal":
            if step.action == "install_package":
                pkg = step.params.get("package", "")
                if pkg:
                    ctx.add_package(pkg)

        # Browser executor outputs
        elif step.executor == "browser":
            if step.action == "search":
                query = step.params.get("query", "")
                ctx.add_browser_result(
                    url=f"https://www.google.com/search?q={query}",
                    snippet=output[:300],
                )
                # Post search results to coding executor
                ctx.post_message(
                    from_executor="browser",
                    to_executor="coding",
                    key="search_results",
                    value=output[:300],
                )
            elif step.action in ("fetch_page", "fetch_snippet"):
                url = step.params.get("url", "")
                ctx.add_browser_result(url=url, snippet=output[:300])

    # ── Console UX ─────────────────────────────────────────────────────────────

    def _print_workflow_header(
        self,
        goal: Goal,
        workflow_name: str,
        workflow_id: str,
        steps: List[WorkflowStep],
        report,
    ) -> None:
        executors_used = sorted({s.executor for s in steps})
        stages         = []
        seen: set      = set()
        for s in steps:
            if s.stage not in seen:
                seen.add(s.stage)
                stages.append(s.stage)

        if _RICH:
            _console.print()
            _console.print(Panel(
                f"[bold white]JARVIS Workflow Orchestrator[/bold white]\n\n"
                f"  [dim]Workflow ID :[/dim] [cyan]{workflow_id}[/cyan]\n"
                f"  [dim]Template    :[/dim] [magenta]{workflow_name}[/magenta]\n"
                f"  [dim]Goal        :[/dim] [bold]{goal.goal}[/bold]\n"
                f"  [dim]Category    :[/dim] [yellow]{goal.category}[/yellow]  "
                f"[dim]Confidence:[/dim] [cyan]{goal.confidence}%[/cyan]\n"
                f"  [dim]Steps       :[/dim] [cyan]{len(steps)}[/cyan]  "
                f"[dim]Stages:[/dim] [cyan]{' → '.join(stages)}[/cyan]\n"
                f"  [dim]Executors   :[/dim] [green]{', '.join(executors_used)}[/green]",
                border_style="bright_blue",
                expand=False,
            ))
            if report.warnings:
                for w in report.warnings:
                    _console.print(f"  [yellow]⚠  {w}[/yellow]")
            _console.print()
        else:
            print(f"\n{'═' * 60}")
            print(f"  JARVIS Workflow Orchestrator")
            print(f"  Workflow ID : {workflow_id}")
            print(f"  Template    : {workflow_name}")
            print(f"  Goal        : {goal.goal}")
            print(f"  Steps       : {len(steps)}")
            print(f"  Executors   : {', '.join(executors_used)}")
            print(f"{'═' * 60}")

    def _print_step_header(
        self, step: WorkflowStep, idx: int, total: int
    ) -> None:
        risk_colours = {
            "safe": "green", "low": "green",
            "medium": "yellow", "high": "red", "critical": "bold red",
        }
        if _RICH:
            colour = risk_colours.get(step.risk_level, "white")
            _console.print(
                f"\n  [dim]Step {idx}/{total}[/dim]  "
                f"[bold]{step.name}[/bold]  "
                f"[[{colour}]{step.risk_level}[/{colour}]]  "
                f"[dim][{step.executor}][/dim]"
            )
        else:
            print(f"\n  Step {idx}/{total}: {step.name}  [{step.risk_level}]  [{step.executor}]")

    def _print_step_result(
        self, step: WorkflowStep, idx: int, total: int
    ) -> None:
        icons = {
            StepStatus.SUCCESS: ("✓", "green"),
            StepStatus.FAILED:  ("✗", "red"),
            StepStatus.DENIED:  ("⊘", "yellow"),
            StepStatus.SKIPPED: ("⊙", "dim"),
            StepStatus.BLOCKED: ("⊡", "dim"),
        }
        icon, colour = icons.get(step.status, ("?", "white"))
        msg = (step.output or step.error or step.status.value)[:120]

        if _RICH:
            _console.print(
                f"  [{colour}]{icon}  {step.status.value.upper()}[/{colour}]"
                f"  [dim]{msg}[/dim]"
            )
        else:
            print(f"  {icon}  {step.status.value.upper()}  {msg}")

    def _print_workflow_summary(
        self, state: WorkflowState, ctx: SharedContext
    ) -> None:
        s = state
        status_colour = {
            WorkflowStatus.COMPLETED:           "green",
            WorkflowStatus.PARTIALLY_COMPLETED: "yellow",
            WorkflowStatus.FAILED:              "red",
            WorkflowStatus.CANCELLED:           "dim",
        }.get(s.status, "white")

        if _RICH:
            # Artifact table
            artifact_lines = []
            if ctx.generated_files:
                artifact_lines.append(
                    f"  [dim]Files     :[/dim] "
                    f"[cyan]{', '.join(ctx.generated_files[:5])}[/cyan]"
                )
            if ctx.created_dirs:
                artifact_lines.append(
                    f"  [dim]Dirs      :[/dim] "
                    f"[cyan]{', '.join(ctx.created_dirs[:5])}[/cyan]"
                )
            if ctx.installed_packages:
                artifact_lines.append(
                    f"  [dim]Packages  :[/dim] "
                    f"[cyan]{', '.join(ctx.installed_packages)}[/cyan]"
                )
            if ctx.browser_results:
                artifact_lines.append(
                    f"  [dim]Searches  :[/dim] "
                    f"[cyan]{len(ctx.browser_results)} result(s)[/cyan]"
                )

            artifact_str = "\n".join(artifact_lines) if artifact_lines else "  [dim](none)[/dim]"

            _console.print()
            _console.print(Panel(
                f"[bold]Workflow {s.status.value.upper()}[/bold]\n\n"
                f"  [{status_colour}]Status    : {s.status.value}[/{status_colour}]\n"
                f"  [green]✓ Success : {len(s.success_steps)}[/green]\n"
                f"  [red]✗ Failed  : {len(s.failed_steps)}[/red]\n"
                f"  [yellow]⊘ Denied  : {len(s.denied_steps)}[/yellow]\n"
                f"  [dim]⊡ Blocked : {len(s.skipped_steps)}[/dim]\n"
                f"  [dim]Duration  : {s.duration_ms:.0f} ms[/dim]\n\n"
                f"[bold]Artifacts[/bold]\n{artifact_str}\n\n"
                f"  [dim]Workspace : {sandbox.root}[/dim]",
                border_style=status_colour,
                expand=False,
            ))
        else:
            print(f"\n{'─' * 60}")
            print(f"  Workflow {s.status.value.upper()}")
            print(f"  ✓ Success : {len(s.success_steps)}")
            print(f"  ✗ Failed  : {len(s.failed_steps)}")
            print(f"  ⊘ Denied  : {len(s.denied_steps)}")
            print(f"  ⊡ Blocked : {len(s.skipped_steps)}")
            if ctx.generated_files:
                print(f"  Files     : {ctx.generated_files[:5]}")
            print(f"{'─' * 60}\n")

    def _print_validation_failure(self, report) -> None:
        if _RICH:
            _console.print()
            _console.print(Panel(
                f"[bold red]Workflow Validation Failed[/bold red]\n\n"
                + "\n".join(f"  [red]✗[/red] {e}" for e in report.errors),
                border_style="red",
                expand=False,
            ))
        else:
            print("\n  Workflow Validation Failed:")
            for e in report.errors:
                print(f"  ✗ {e}")


# Module-level singleton
workflow_orchestrator = WorkflowOrchestrator()
