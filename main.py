"""
main.py
=======
JARVIS v0.3 — Main entry point.

Pipeline per user input
-----------------------
  Input → Brain (classify) → Planner (plan) → [Execute? Y/N] → ExecutionManager
"""

import logging

from core.config import config
from core.brain import brain
from core.planner import planner
from core.skills import skill_registry
from core.memory import memory_system
from core.models import MemoryRecord

logger = logging.getLogger(__name__)

# ── Rich console ───────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule
    _console = Console()
    _RICH = True
except ImportError:
    _RICH = False
    _console = None


def _print(msg: str) -> None:
    if _RICH:
        _console.print(msg)
    else:
        print(msg)


def _ask_execute() -> bool:
    """Ask the user whether to execute the generated plan."""
    print()
    while True:
        try:
            answer = input("  Execute this plan? [Y/N] > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter Y or N.")


def main():
    # Run recovery check
    from autonomy.recovery_manager import recovery_manager
    recovery_manager.run_recovery_check()

    _print(f"\n[bold cyan]JARVIS v{config.jarvis_version}[/bold cyan] Ready\n"
           if _RICH else f"\nJARVIS v{config.jarvis_version} Ready\n")

    # Lazy-import execution manager (avoids circular imports at module level)
    from skills.execution.manager import execution_manager

    try:
        while True:
            try:
                user_input = input("You > ").strip()

                if not user_input:
                    continue

                # ── Built-in commands ──────────────────────────────────────────
                if user_input.lower() in ("exit", "quit", "q"):
                    _print("\nJARVIS shutting down...")
                    break

                if user_input.lower() == "history":
                    _show_history()
                    continue

                if user_input.lower().startswith("remember "):
                    _remember(user_input[9:].strip())
                    continue

                if user_input.lower() == "exec history":
                    _show_exec_history()
                    continue

                if user_input.lower() == "workflow history":
                    _show_workflow_history()
                    continue

                if user_input.lower().startswith("control "):
                    _run_control_command(user_input[8:].strip())
                    continue

                if user_input.lower() == "control history":
                    _show_control_history()
                    continue

                # ── Brain analysis ─────────────────────────────────────────────
                logger.info(f"Task received: {user_input}")
                goal = brain.analyze_task(user_input)

                # Internal commands (debug toggle, etc.)
                if goal.category == "internal_commands":
                    _print(
                        f"\n[bold]JARVIS[/bold]\nCommand executed: {goal.intent_summary}\n"
                        if _RICH else f"\nJARVIS\nCommand executed: {goal.intent_summary}\n"
                    )
                    continue

                # Unknown intent
                if goal.category == "unknown":
                    _print(
                        "\n[bold]JARVIS[/bold]\n"
                        "[yellow]Unable to determine intent with sufficient confidence.[/yellow]\n"
                        "Please provide a clearer task.\n"
                        if _RICH else
                        "\nJARVIS\nUnable to determine intent. Please provide a clearer task.\n"
                    )
                    continue

                # ── Plan ───────────────────────────────────────────────────────
                plan = planner.create_plan(goal)
                suggested_skills = skill_registry.recommend_skills(
                    goal.category, goal.goal
                )

                # ── Display analysis ───────────────────────────────────────────
                _display_analysis(goal, plan, suggested_skills)

                # ── Save to memory ─────────────────────────────────────────────
                record = MemoryRecord(
                    task=user_input,
                    goal=goal,
                    plan=plan,
                    suggested_skills=suggested_skills,
                )
                memory_system.save_task(record)

                # ── Ask to execute ─────────────────────────────────────────────
                if _ask_execute():
                    if goal.category == "computer_control":
                        from computer_control.control_workflow_generator import control_workflow_generator
                        from computer_control.control_manager import control_manager
                        control_actions = control_workflow_generator.generate_from_input(
                            user_input, goal.category, goal.requirements
                        )
                        if control_actions:
                            control_manager.execute_actions(
                                control_actions, goal=goal.goal
                            )
                        else:
                            _print(
                                "\n[bold]JARVIS[/bold]\n[yellow]Could not map that to a desktop action. "
                                "Try: 'move mouse to center', 'open chrome', 'take screenshot'[/yellow]\n"
                                if _RICH else
                                "\nJARVIS\nCould not map to a desktop action.\n"
                            )
                    elif goal.category in ["text_to_speech", "speech_control", "voice_interaction"]:
                        # Handle voice actions with voice executor!
                        from brain.voice_workflow_generator import voice_workflow_generator
                        from skills.execution.manager import execution_manager
                        # Use voice workflow generator and let execution manager handle steps!
                        voice_actions = voice_workflow_generator.generate_from_input(
                            user_input, goal.category, goal.requirements
                        )
                        if voice_actions:
                            # Use task router to create steps, then execute!
                            from skills.execution.task_router import task_router
                            execution_steps = task_router.route(goal)
                            result = execution_manager.execute(goal)
                        else:
                            _print(
                                "\n[bold]JARVIS[/bold]\n[yellow]Could not map that to a voice action. "
                                "Try: 'speak hello', 'stop speaking', 'talk to me'[/yellow]\n"
                                if _RICH else
                                "\nJARVIS\nCould not map to a voice action.\n"
                            )
                    else:
                        from orchestration.workflow_orchestrator import workflow_orchestrator
                        workflow_orchestrator.run(goal)
                else:
                    _print(
                        "\n  [dim]Execution skipped. Plan saved to memory.[/dim]\n"
                        if _RICH else "\n  Execution skipped. Plan saved to memory.\n"
                    )

            except ValueError as ve:
                _print(
                    f"\n[bold]JARVIS[/bold]\n[red]{ve}[/red]\nPlease provide a clearer task.\n"
                    if _RICH else f"\nJARVIS\n{ve}\nPlease provide a clearer task.\n"
                )
            except KeyboardInterrupt:
                _print("\n\nJARVIS shutting down...")
                break
            except Exception as exc:
                logger.error(f"Error processing request: {exc}", exc_info=True)
                _print(
                    f"\n[bold]JARVIS[/bold]\n[red]Error: {exc}[/red]\n"
                    if _RICH else f"\nJARVIS\nError: {exc}\n"
                )

    finally:
        from database.mongodb import mongodb
        mongodb.close()


# ── Helper display functions ───────────────────────────────────────────────────

def _display_analysis(goal, plan, suggested_skills) -> None:
    if _RICH:
        from rich.table import Table
        from rich import box

        _console.print()
        _console.print(Panel(
            f"[bold white]Goal Identified[/bold white]\n\n"
            f"  [dim]Input     :[/dim] {goal.goal}\n"
            f"  [dim]Category  :[/dim] [magenta]{goal.category.replace('_', ' ').title()}[/magenta]\n"
            f"  [dim]Confidence:[/dim] [cyan]{goal.confidence}%[/cyan]",
            border_style="bright_blue",
            expand=False,
        ))

        if goal.requirements:
            _console.print("\n  [bold]Requirements:[/bold]")
            for req in goal.requirements:
                _console.print(f"    [cyan]•[/cyan] {req}")

        if suggested_skills:
            _console.print("\n  [bold]Suggested Skills:[/bold]")
            for skill in suggested_skills:
                _console.print(f"    [green]•[/green] {skill.name}")

        _console.print("\n  [bold]Execution Plan:[/bold]")
        for i, step in enumerate(plan.steps, 1):
            _console.print(f"    [dim]{i}.[/dim] {step}")

        _console.print()
    else:
        print(f"\nJARVIS")
        print(f"\nGoal     : {goal.goal}")
        print(f"Category : {goal.category}")
        print(f"Confidence: {goal.confidence}%")
        if goal.requirements:
            print("\nRequirements:")
            for req in goal.requirements:
                print(f"  * {req}")
        if suggested_skills:
            print("\nSuggested Skills:")
            for skill in suggested_skills:
                print(f"  * {skill.name}")
        print("\nExecution Plan:")
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. {step}")
        print()


def _show_history() -> None:
    history = memory_system.get_history()
    if _RICH:
        _console.print("\n[bold]--- Task History ---[/bold]")
        if not history:
            _console.print("[dim]No tasks found.[/dim]")
        else:
            for i, task in enumerate(history, 1):
                _console.print(
                    f"\n  [cyan]{i}.[/cyan] {task['task']}\n"
                    f"     Category  : {task['goal']['category']}\n"
                    f"     Confidence: {task['goal'].get('confidence', 'N/A')}%\n"
                    f"     Time      : {task['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                )
        _console.print()
    else:
        print("\n--- Task History ---")
        if not history:
            print("No tasks found.")
        else:
            for i, task in enumerate(history, 1):
                print(f"\n{i}. {task['task']}")
                print(f"   Category: {task['goal']['category']}")
                print(f"   Time: {task['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def _remember(value: str) -> None:
    if value:
        memory_system.save_preference("user_preference", value)
        _print(
            f"\n[bold]JARVIS[/bold]\nRemembered: [cyan]{value}[/cyan]\n"
            if _RICH else f"\nJARVIS\nRemembered: {value}\n"
        )
    else:
        _print(
            "\n[bold]JARVIS[/bold]\nUsage: remember <something>\n"
            if _RICH else "\nJARVIS\nUsage: remember <something>\n"
        )


def _show_exec_history() -> None:
    from skills.execution.execution_history import execution_history
    recent = execution_history.get_recent(10)
    if _RICH:
        _console.print("\n[bold]--- Execution History (last 10) ---[/bold]")
        if not recent:
            _console.print("[dim]No executions recorded.[/dim]")
        else:
            for ctx in recent:
                colour = "green" if ctx.status.value == "success" else "red"
                _console.print(
                    f"  [{colour}]{ctx.status.value:<8}[/{colour}]  "
                    f"[dim]{ctx.executor}.{ctx.action}[/dim]  "
                    f"[cyan]{ctx.task_id}[/cyan]"
                )
        _console.print()
    else:
        print("\n--- Execution History (last 10) ---")
        for ctx in recent:
            print(f"  {ctx.status.value:<8}  {ctx.executor}.{ctx.action}  {ctx.task_id}")
        print()


def _show_workflow_history() -> None:
    from orchestration.workflow_memory import workflow_memory
    recent = workflow_memory.get_recent(10)
    if _RICH:
        _console.print("\n[bold]--- Workflow History (last 10) ---[/bold]")
        if not recent:
            _console.print("[dim]No workflows recorded.[/dim]")
        else:
            for wf in recent:
                colour = "green" if wf.status.value == "completed" else "yellow"
                _console.print(
                    f"  [{colour}]{wf.status.value:<20}[/{colour}]  "
                    f"[magenta]{wf.workflow_name:<20}[/magenta]  "
                    f"[dim]{wf.goal_text[:50]}[/dim]"
                )
        _console.print()
    else:
        print("\n--- Workflow History (last 10) ---")
        for wf in recent:
            print(f"  {wf.status.value:<20}  {wf.workflow_name:<20}  {wf.goal_text[:50]}")
        print()


def _run_control_command(command: str) -> None:
    """
    Handle 'control <workflow_name> [args]' commands.

    Examples
    --------
    control open_chrome_and_search latest AI models
    control open_app_workflow notepad
    control screenshot_workflow
    control create_notepad_file Hello from JARVIS
    """
    from computer_control.control_manager import control_manager

    parts = command.split(None, 1)
    workflow_name = parts[0] if parts else ""
    arg           = parts[1] if len(parts) > 1 else ""

    if not workflow_name:
        _print(
            "\n[bold]JARVIS[/bold]\nUsage: control <workflow> [args]\n"
            "Available: open_chrome_and_search, open_app_workflow, "
            "create_notepad_file, browser_search_workflow, screenshot_workflow\n"
            if _RICH else
            "\nJARVIS\nUsage: control <workflow> [args]\n"
        )
        return

    try:
        kwargs: dict = {}
        if workflow_name == "open_chrome_and_search":
            kwargs = {"query": arg or "latest AI news"}
        elif workflow_name == "open_app_workflow":
            kwargs = {"app_name": arg or "notepad"}
        elif workflow_name == "create_notepad_file":
            kwargs = {"content": arg or "Hello from JARVIS", "filename": "jarvis_note.txt"}
        elif workflow_name == "browser_search_workflow":
            kwargs = {"query": arg or "latest AI models", "engine": "google"}
        elif workflow_name == "screenshot_workflow":
            kwargs = {}
        else:
            kwargs = {}

        control_manager.run_workflow(workflow_name, **kwargs)

    except ValueError as ve:
        _print(
            f"\n[bold]JARVIS[/bold]\n[red]{ve}[/red]\n"
            if _RICH else f"\nJARVIS\n{ve}\n"
        )
    except Exception as exc:
        logger.error(f"Control command error: {exc}", exc_info=True)
        _print(
            f"\n[bold]JARVIS[/bold]\n[red]Control error: {exc}[/red]\n"
            if _RICH else f"\nJARVIS\nControl error: {exc}\n"
        )


def _show_control_history() -> None:
    from computer_control.action_queue import ActionQueue
    from computer_control.control_manager import control_manager
    # Read from log file
    from pathlib import Path
    import json
    log_dir = Path(__file__).parent / "logs" / "control_logs"
    if not log_dir.exists():
        _print("\n[dim]No control history found.[/dim]\n" if _RICH else "\nNo control history.\n")
        return
    files = sorted(log_dir.glob("*.jsonl"), reverse=True)
    if not files:
        _print("\n[dim]No control history found.[/dim]\n" if _RICH else "\nNo control history.\n")
        return
    lines = files[0].read_text(encoding="utf-8").strip().splitlines()[-10:]
    if _RICH:
        _console.print("\n[bold]--- Control History (last 10 sessions) ---[/bold]")
        for line in lines:
            try:
                d = json.loads(line)
                colour = "green" if d.get("success_count", 0) > 0 else "yellow"
                _console.print(
                    f"  [{colour}]✓ {d.get('success_count',0)}[/{colour}]  "
                    f"[red]✗ {d.get('failed_count',0)}[/red]  "
                    f"[dim]{d.get('goal','')[:50]}[/dim]"
                )
            except Exception:
                pass
        _console.print()
    else:
        print("\n--- Control History ---")
        for line in lines:
            try:
                d = json.loads(line)
                print(f"  ✓{d.get('success_count',0)} ✗{d.get('failed_count',0)}  {d.get('goal','')[:50]}")
            except Exception:
                pass
        print()


if __name__ == "__main__":
    main()
