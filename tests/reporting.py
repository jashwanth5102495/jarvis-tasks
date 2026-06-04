"""
reporting.py
============
All console and file output for the JARVIS QA framework.
Uses `rich` for beautiful terminal rendering.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from typing import List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from tests.validators import TestResult, CheckResult

console = Console()

# ─────────────────────────────────────────────────────────────────────────────
# Colour palette
# ─────────────────────────────────────────────────────────────────────────────
PASS_STYLE  = "bold green"
FAIL_STYLE  = "bold red"
WARN_STYLE  = "bold yellow"
INFO_STYLE  = "bold cyan"
DIM_STYLE   = "dim"
HEADER_STYLE = "bold white on dark_blue"

CATEGORY_COLOURS = {
    "design":               "magenta",
    "software_development": "cyan",
    "system_operations":    "yellow",
    "communication":        "blue",
    "research":             "green",
    "automation":           "orange3",
    "internal_commands":    "bright_white",
    "productivity":         "light_green",
    "business":             "gold1",
    "general":              "grey70",
    "unknown":              "red",
}


def _cat_text(cat: str | None) -> Text:
    colour = CATEGORY_COLOURS.get(cat or "unknown", "white")
    return Text(cat or "—", style=colour)


def _conf_text(conf: float | None) -> Text:
    if conf is None:
        return Text("—", style=DIM_STYLE)
    if conf >= 80:
        style = PASS_STYLE
    elif conf >= 60:
        style = WARN_STYLE
    else:
        style = FAIL_STYLE
    return Text(f"{conf:.1f}%", style=style)


# ─────────────────────────────────────────────────────────────────────────────
# Header / footer banners
# ─────────────────────────────────────────────────────────────────────────────

def print_header(suite_name: str, total: int) -> None:
    console.print()
    console.print(Panel(
        f"[bold white]JARVIS QA Test Runner[/bold white]\n"
        f"[dim]Suite:[/dim] [cyan]{suite_name}[/cyan]   "
        f"[dim]Cases:[/dim] [cyan]{total}[/cyan]   "
        f"[dim]Started:[/dim] [cyan]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/cyan]",
        style="dark_blue",
        border_style="bright_blue",
        expand=False,
    ))
    console.print()


def print_footer() -> None:
    console.print()
    console.print(Rule(style="bright_blue"))


# ─────────────────────────────────────────────────────────────────────────────
# Per-case detail card
# ─────────────────────────────────────────────────────────────────────────────

def print_case_detail(result: TestResult, verbose: bool = False) -> None:
    status_text = Text("  PASS  ", style="bold white on green") if result.passed \
                  else Text("  FAIL  ", style="bold white on red")

    # Build header line
    header = Text()
    header.append(f"#{result.index:>3}  ", style="dim")
    header.append(status_text)
    header.append(f"  {result.input_text!r}", style="bold")

    console.print(header)

    if verbose or not result.passed:
        tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        tbl.add_column("key",   style="dim",   no_wrap=True)
        tbl.add_column("value", no_wrap=False)

        tbl.add_row("Expected",   _cat_text(result.expected_category))
        tbl.add_row("Actual",     _cat_text(result.actual_category))
        tbl.add_row("Confidence", _conf_text(result.confidence))

        if result.requirements:
            tbl.add_row("Requirements", Text(", ".join(result.requirements), style="dim"))

        tbl.add_row("Time", Text(f"{result.elapsed_ms:.1f} ms", style=DIM_STYLE))

        if result.error:
            tbl.add_row("Error", Text(result.error, style=FAIL_STYLE))

        # Individual check outcomes
        for chk in result.checks:
            icon = "✓" if chk.passed else "✗"
            style = PASS_STYLE if chk.passed else FAIL_STYLE
            detail = f"{chk.expected} → {chk.actual}"
            if chk.detail:
                detail += f"  ({chk.detail})"
            tbl.add_row(
                f"  {icon} {chk.name}",
                Text(detail, style=style),
            )

        console.print(tbl)


# ─────────────────────────────────────────────────────────────────────────────
# Progress bar factory
# ─────────────────────────────────────────────────────────────────────────────

def make_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[cyan]{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Summary report
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(results: List[TestResult]) -> None:
    total   = len(results)
    passed  = sum(1 for r in results if r.passed)
    failed  = total - passed
    accuracy = (passed / total * 100) if total else 0.0

    # ── Overall panel ────────────────────────────────────────────────────────
    acc_style = PASS_STYLE if accuracy >= 90 else (WARN_STYLE if accuracy >= 70 else FAIL_STYLE)
    console.print()
    console.print(Panel(
        f"[bold white]JARVIS TEST SUMMARY[/bold white]\n\n"
        f"  Total Tests : [cyan]{total}[/cyan]\n"
        f"  Passed      : [green]{passed}[/green]\n"
        f"  Failed      : [red]{failed}[/red]\n"
        f"  Accuracy    : [{acc_style}]{accuracy:.1f}%[/{acc_style}]",
        style="dark_blue",
        border_style="bright_blue",
        expand=False,
    ))

    # ── Per-category accuracy table ──────────────────────────────────────────
    cat_total:  dict[str, int] = defaultdict(int)
    cat_passed: dict[str, int] = defaultdict(int)

    for r in results:
        cat = r.expected_category
        cat_total[cat] += 1
        if r.passed:
            cat_passed[cat] += 1

    cat_tbl = Table(
        title="Category Accuracy",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style=HEADER_STYLE,
        show_lines=False,
    )
    cat_tbl.add_column("Category",  style="bold", no_wrap=True)
    cat_tbl.add_column("Passed",    justify="right")
    cat_tbl.add_column("Total",     justify="right")
    cat_tbl.add_column("Accuracy",  justify="right")
    cat_tbl.add_column("Bar",       no_wrap=True)

    for cat in sorted(cat_total.keys()):
        p = cat_passed[cat]
        t = cat_total[cat]
        pct = (p / t * 100) if t else 0.0
        bar_len = int(pct / 5)          # max 20 chars
        bar = "█" * bar_len + "░" * (20 - bar_len)
        pct_style = PASS_STYLE if pct >= 90 else (WARN_STYLE if pct >= 70 else FAIL_STYLE)
        cat_tbl.add_row(
            _cat_text(cat),
            str(p),
            str(t),
            Text(f"{pct:.0f}%", style=pct_style),
            Text(bar, style=CATEGORY_COLOURS.get(cat, "white")),
        )

    console.print()
    console.print(cat_tbl)

    # ── Confidence distribution ───────────────────────────────────────────────
    confs = [r.confidence for r in results
             if r.confidence is not None and r.expected_category != "internal_commands"]
    if confs:
        avg_conf = sum(confs) / len(confs)
        min_conf = min(confs)
        max_conf = max(confs)
        console.print()
        console.print(
            f"  [dim]Confidence stats:[/dim]  "
            f"avg [cyan]{avg_conf:.1f}%[/cyan]  "
            f"min [yellow]{min_conf:.1f}%[/yellow]  "
            f"max [green]{max_conf:.1f}%[/green]"
        )

    # ── Timing ───────────────────────────────────────────────────────────────
    times = [r.elapsed_ms for r in results]
    if times:
        console.print(
            f"  [dim]Timing:[/dim]  "
            f"avg [cyan]{sum(times)/len(times):.1f} ms[/cyan]  "
            f"total [cyan]{sum(times):.0f} ms[/cyan]"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Failure report
# ─────────────────────────────────────────────────────────────────────────────

def print_failure_report(results: List[TestResult]) -> None:
    failures = [r for r in results if not r.passed]
    if not failures:
        console.print()
        console.print(Panel(
            "[bold green]All tests passed — no failures to report.[/bold green]",
            border_style="green",
            expand=False,
        ))
        return

    console.print()
    console.print(Rule("[bold red]FAILED TESTS[/bold red]", style="red"))

    fail_tbl = Table(
        box=box.ROUNDED,
        border_style="red",
        header_style="bold white on red",
        show_lines=True,
    )
    fail_tbl.add_column("#",         justify="right", style="dim", width=4)
    fail_tbl.add_column("Input",     style="bold",    no_wrap=False)
    fail_tbl.add_column("Expected",  no_wrap=True)
    fail_tbl.add_column("Actual",    no_wrap=True)
    fail_tbl.add_column("Conf",      justify="right", no_wrap=True)
    fail_tbl.add_column("Failed Checks", no_wrap=False)

    for r in failures:
        failed_check_names = ", ".join(c.name for c in r.failed_checks) or (r.error or "—")
        fail_tbl.add_row(
            str(r.index),
            r.input_text,
            _cat_text(r.expected_category),
            _cat_text(r.actual_category) if r.actual_category else Text("rejected", style="red"),
            _conf_text(r.confidence),
            Text(failed_check_names, style=FAIL_STYLE),
        )

    console.print(fail_tbl)


# ─────────────────────────────────────────────────────────────────────────────
# File output
# ─────────────────────────────────────────────────────────────────────────────

def save_results(results: List[TestResult], output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── JSON ─────────────────────────────────────────────────────────────────
    json_path = os.path.join(output_dir, f"test_results_{ts}.json")
    payload = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "results": [
            {
                "index":             r.index,
                "input":             r.input_text,
                "expected_category": r.expected_category,
                "actual_category":   r.actual_category,
                "confidence":        r.confidence,
                "requirements":      r.requirements,
                "passed":            r.passed,
                "rejected":          r.rejected,
                "elapsed_ms":        round(r.elapsed_ms, 2),
                "error":             r.error,
                "tags":              r.tags,
                "checks": [
                    {
                        "name":     c.name,
                        "passed":   c.passed,
                        "expected": str(c.expected),
                        "actual":   str(c.actual),
                        "detail":   c.detail,
                    }
                    for c in r.checks
                ],
            }
            for r in results
        ],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # ── Plain-text summary ────────────────────────────────────────────────────
    txt_path = os.path.join(output_dir, f"test_summary_{ts}.txt")
    total   = len(results)
    passed  = sum(1 for r in results if r.passed)
    failed  = total - passed
    accuracy = (passed / total * 100) if total else 0.0

    lines = [
        "=" * 60,
        "JARVIS TEST SUMMARY",
        f"Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total     : {total}",
        f"Passed    : {passed}",
        f"Failed    : {failed}",
        f"Accuracy  : {accuracy:.1f}%",
        "=" * 60,
        "",
        "CATEGORY ACCURACY",
        "-" * 40,
    ]

    from collections import defaultdict
    cat_total:  dict[str, int] = defaultdict(int)
    cat_passed: dict[str, int] = defaultdict(int)
    for r in results:
        cat_total[r.expected_category] += 1
        if r.passed:
            cat_passed[r.expected_category] += 1

    for cat in sorted(cat_total.keys()):
        p = cat_passed[cat]
        t = cat_total[cat]
        pct = (p / t * 100) if t else 0.0
        lines.append(f"  {cat:<30} {p}/{t}  ({pct:.0f}%)")

    lines += ["", "FAILED TESTS", "-" * 40]
    failures = [r for r in results if not r.passed]
    if not failures:
        lines.append("  None — all tests passed.")
    else:
        for r in failures:
            lines.append(f"  #{r.index:>3}  {r.input_text!r}")
            lines.append(f"         Expected : {r.expected_category}")
            lines.append(f"         Actual   : {r.actual_category}")
            lines.append(f"         Conf     : {r.confidence}")
            for c in r.failed_checks:
                lines.append(f"         ✗ {c.name}: expected {c.expected}, got {c.actual}")
            lines.append("")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    console.print()
    console.print(
        f"  [dim]Results saved →[/dim]  "
        f"[cyan]{json_path}[/cyan]"
    )
    console.print(
        f"  [dim]Summary saved →[/dim]  "
        f"[cyan]{txt_path}[/cyan]"
    )
