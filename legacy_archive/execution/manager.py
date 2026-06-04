"""
manager.py
==========
ExecutionManager — the central orchestrator for Milestone 2.

Pipeline
--------
Goal → TaskRouter → [ExecutionStep, …]
                         ↓
                  PermissionManager.request(ctx)
                         ↓ approved
                  Executor.execute(ctx)
                         ↓
                  ExecutionHistory.record(ctx)
                         ↓
                  Console UX output

The manager never crashes the system on partial failure.
Each step is independent; a failed step is logged and skipped.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from core.models import Goal
from skills.execution.execution_context import (
    ExecutionContext,
    ExecutionStatus,
    RiskLevel,
)
from skills.execution.execution_history import execution_history
from skills.execution.permissions import permission_manager
from skills.execution.sandbox import sandbox
from skills.execution.task_router import task_router, ExecutionStep

logger = logging.getLogger(__name__)

# Rich is available — use it for the execution UX
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    _console = Console()
    _RICH = True
except ImportError:
    _RICH = False
    _console = None  # type: ignore


class ExecutionResult:
    """Aggregated result of a full task execution."""

    def __init__(self, task_id: str, goal: Goal):
        self.task_id:  str                    = task_id
        self.goal:     Goal                   = goal
        self.contexts: List[ExecutionContext] = []

    @property
    def success_count(self) -> int:
        return sum(1 for c in self.contexts if c.status == ExecutionStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.contexts if c.status == ExecutionStatus.FAILED)

    @property
    def denied_count(self) -> int:
        return sum(1 for c in self.contexts if c.status == ExecutionStatus.DENIED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for c in self.contexts if c.status == ExecutionStatus.SKIPPED)

    @property
    def all_succeeded(self) -> bool:
        return self.failed_count == 0 and len(self.contexts) > 0

    def summary_lines(self) -> List[str]:
        lines = []
        for ctx in self.contexts:
            icon = {
                ExecutionStatus.SUCCESS:  "✓",
                ExecutionStatus.FAILED:   "✗",
                ExecutionStatus.DENIED:   "⊘",
                ExecutionStatus.SKIPPED:  "⊙",
                ExecutionStatus.RUNNING:  "…",
            }.get(ctx.status, "?")
            lines.append(f"  {icon}  {ctx.action}  [{ctx.executor}]")
        return lines


class ExecutionManager:
    """
    Orchestrates the full execution pipeline for a classified Goal.

    Usage
    -----
    result = execution_manager.execute(goal)
    """

    def __init__(self):
        self._executors: Dict[str, Any] = {}
        self._register_executors()

    # ── Executor registry ──────────────────────────────────────────────────────

    def _register_executors(self) -> None:
        """Lazy-import executors to avoid circular imports at module load."""
        from skills.executors.file_executor     import FileExecutor
        from skills.executors.terminal_executor import TerminalExecutor
        from skills.executors.browser_executor  import BrowserExecutor
        from skills.executors.coding_executor   import CodingExecutor
        from skills.executors.voice_executor    import VoiceExecutor

        self._executors = {
            "file":     FileExecutor(),
            "terminal": TerminalExecutor(),
            "browser":  BrowserExecutor(),
            "coding":   CodingExecutor(),
            "voice":    VoiceExecutor(),
        }
        logger.info(f"Registered executors: {list(self._executors.keys())}")

    def register_executor(self, name: str, executor: Any) -> None:
        """Plug in a new executor at runtime."""
        self._executors[name] = executor
        logger.info(f"Executor registered: {name}")

    # ── Main entry point ───────────────────────────────────────────────────────

    def execute(self, goal: Goal) -> ExecutionResult:
        task_id = str(uuid.uuid4())[:12]
        result  = ExecutionResult(task_id=task_id, goal=goal)

        self._print_execution_header(goal, task_id)

        # 1. Route goal → steps
        steps = task_router.route(goal)
        if not steps:
            logger.warning(f"No steps generated for category={goal.category!r}")
            self._print_no_steps()
            return result

        # 2. Execute each step
        for idx, step in enumerate(steps, start=1):
            ctx = self._build_context(task_id, step)
            result.contexts.append(ctx)
            self._execute_step(idx, len(steps), step, ctx)

        # 3. Final summary
        self._print_execution_summary(result)
        return result

    # ── Step execution ─────────────────────────────────────────────────────────

    def _execute_step(
        self,
        idx: int,
        total: int,
        step: ExecutionStep,
        ctx: ExecutionContext,
    ) -> None:
        description = step.get("description", ctx.action)
        self._print_step_header(idx, total, description, ctx.risk_level)

        # Permission gate
        approved = permission_manager.request(ctx)
        if not approved:
            execution_history.record(ctx)
            self._print_step_result(ctx)
            return

        # Resolve executor
        executor = self._executors.get(ctx.executor)
        if executor is None:
            ctx.mark_failed(f"Unknown executor: {ctx.executor!r}")
            execution_history.record(ctx)
            self._print_step_result(ctx)
            return

        # Run
        ctx.mark_running()
        try:
            output = executor.execute(ctx)
            ctx.mark_success(output or "")
        except Exception as exc:
            logger.error(f"Executor error [{ctx.executor}.{ctx.action}]: {exc}", exc_info=True)
            ctx.mark_failed(str(exc))

        execution_history.record(ctx)
        self._print_step_result(ctx)

    # ── Context builder ────────────────────────────────────────────────────────

    @staticmethod
    def _build_context(task_id: str, step: ExecutionStep) -> ExecutionContext:
        return ExecutionContext(
            task_id    = task_id,
            executor   = step["executor"],
            action     = step["action"],
            params     = step.get("params", {}),
            risk_level = step.get("risk_level", RiskLevel.SAFE),
        )

    # ── Console UX ─────────────────────────────────────────────────────────────

    def _print_execution_header(self, goal: Goal, task_id: str) -> None:
        if _RICH:
            _console.print()
            _console.print(Panel(
                f"[bold white]JARVIS Execution Engine[/bold white]\n"
                f"[dim]Task ID :[/dim] [cyan]{task_id}[/cyan]\n"
                f"[dim]Goal    :[/dim] [bold]{goal.goal}[/bold]\n"
                f"[dim]Category:[/dim] [magenta]{goal.category}[/magenta]  "
                f"[dim]Confidence:[/dim] [cyan]{goal.confidence}%[/cyan]",
                border_style="bright_blue",
                expand=False,
            ))
        else:
            print(f"\n{'═' * 56}")
            print(f"  JARVIS Execution Engine")
            print(f"  Task ID  : {task_id}")
            print(f"  Goal     : {goal.goal}")
            print(f"  Category : {goal.category}")
            print(f"{'═' * 56}")

    def _print_step_header(
        self,
        idx: int,
        total: int,
        description: str,
        risk: RiskLevel,
    ) -> None:
        risk_colours = {
            RiskLevel.SAFE:     "green",
            RiskLevel.LOW:      "green",
            RiskLevel.MEDIUM:   "yellow",
            RiskLevel.HIGH:     "red",
            RiskLevel.CRITICAL: "bold red",
        }
        if _RICH:
            colour = risk_colours.get(risk, "white")
            _console.print(
                f"\n  [dim]Step {idx}/{total}[/dim]  "
                f"[bold]{description}[/bold]  "
                f"[[{colour}]{risk.value}[/{colour}]]"
            )
        else:
            print(f"\n  Step {idx}/{total}: {description}  [{risk.value}]")

    def _print_step_result(self, ctx: ExecutionContext) -> None:
        status_map = {
            ExecutionStatus.SUCCESS:  ("\033[92m✓\033[0m", "green"),
            ExecutionStatus.FAILED:   ("\033[91m✗\033[0m", "red"),
            ExecutionStatus.DENIED:   ("\033[93m⊘\033[0m", "yellow"),
            ExecutionStatus.SKIPPED:  ("\033[90m⊙\033[0m", "dim"),
        }
        plain_icon, rich_colour = status_map.get(
            ctx.status, ("?", "white")
        )

        if _RICH:
            msg = ctx.output or ctx.error or ctx.status.value
            _console.print(
                f"  [{rich_colour}]{plain_icon}  {ctx.status.value.upper()}[/{rich_colour}]"
                f"  [dim]{msg[:120]}[/dim]"
            )
        else:
            msg = ctx.output or ctx.error or ctx.status.value
            print(f"  {plain_icon}  {ctx.status.value.upper()}  {msg[:120]}")

    def _print_execution_summary(self, result: ExecutionResult) -> None:
        if _RICH:
            colour = "green" if result.all_succeeded else "yellow"
            _console.print()
            _console.print(Panel(
                f"[bold]Execution Complete[/bold]\n\n"
                f"  [green]✓ Success :[/green] {result.success_count}\n"
                f"  [red]✗ Failed  :[/red] {result.failed_count}\n"
                f"  [yellow]⊘ Denied  :[/yellow] {result.denied_count}\n"
                f"  [dim]⊙ Skipped :[/dim] {result.skipped_count}\n\n"
                f"  [dim]Workspace :[/dim] [cyan]{sandbox.root}[/cyan]",
                border_style=colour,
                expand=False,
            ))
        else:
            print(f"\n{'─' * 56}")
            print(f"  Execution Complete")
            print(f"  ✓ Success : {result.success_count}")
            print(f"  ✗ Failed  : {result.failed_count}")
            print(f"  ⊘ Denied  : {result.denied_count}")
            print(f"  ⊙ Skipped : {result.skipped_count}")
            print(f"{'─' * 56}\n")

    def _print_no_steps(self) -> None:
        if _RICH:
            _console.print("\n  [yellow]No executable steps generated for this goal.[/yellow]\n")
        else:
            print("\n  No executable steps generated for this goal.\n")


# Module-level singleton
execution_manager = ExecutionManager()
