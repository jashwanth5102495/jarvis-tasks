"""
test_runner.py
==============
JARVIS Automated QA Test Runner
--------------------------------
Usage
-----
  # Run all suites (default)
  python -m tests.test_runner

  # Run a specific suite
  python -m tests.test_runner --suite design
  python -m tests.test_runner --suite software
  python -m tests.test_runner --suite stress

  # Verbose mode (show detail for every case, not just failures)
  python -m tests.test_runner --verbose

  # Enable brain debug output during tests
  python -m tests.test_runner --debug

  # Skip saving results to disk
  python -m tests.test_runner --no-save

  # Run stress suite with concurrency
  python -m tests.test_runner --suite stress --workers 8 --repeat 2

Available suites
----------------
  all, design, software, system_ops, communication,
  research, automation, internal, invalid, synonym, stress
"""

from __future__ import annotations

import argparse
import os
import sys
import time

# ── Path bootstrap ────────────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Imports ───────────────────────────────────────────────────────────────────
from rich.console import Console
from rich.rule import Rule

from tests.test_cases import SUITES, ALL_TEST_CASES
from tests.validators import TestValidator, TestResult
from tests.reporting import (
    console,
    make_progress,
    print_case_detail,
    print_failure_report,
    print_footer,
    print_header,
    print_summary,
    save_results,
)
from tests.stress_tests import run_stress_test

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="JARVIS Automated QA Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--suite",
        default="all",
        choices=list(SUITES.keys()),
        help="Test suite to run (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detail for every test case, not just failures",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable JARVIS brain debug output during tests",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Skip saving results to disk",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Thread-pool size for stress tests (default: 4)",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Repeat stress suite N times (default: 1)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(ROOT, "tests", "results"),
        help="Directory for saved results (default: tests/results/)",
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_suite(
    suite_name: str,
    verbose: bool,
    debug: bool,
    workers: int,
    repeat: int,
) -> list[TestResult]:
    """Execute a named suite and return all TestResult objects."""

    # Import Brain here so path is already set up
    from core.brain import Brain

    brain = Brain()
    brain.debug_info.enabled = debug

    cases = SUITES[suite_name]

    # Stress suite uses concurrent runner
    if suite_name == "stress":
        return run_stress_test(brain, workers=workers, repeat=repeat)

    validator = TestValidator(brain)
    results: list[TestResult] = []

    print_header(suite_name, len(cases))

    with make_progress() as progress:
        task_id = progress.add_task(
            f"[cyan]Running {suite_name}…", total=len(cases)
        )

        for idx, case in enumerate(cases, start=1):
            result = validator.run(case, idx)
            results.append(result)
            progress.advance(task_id)

            # Always print failures inline; verbose prints everything
            if not result.passed or verbose:
                progress.stop()
                print_case_detail(result, verbose=verbose)
                progress.start()

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()

    t_start = time.perf_counter()

    results = run_suite(
        suite_name=args.suite,
        verbose=args.verbose,
        debug=args.debug,
        workers=args.workers,
        repeat=args.repeat,
    )

    elapsed_total = (time.perf_counter() - t_start) * 1000

    # ── Reports ───────────────────────────────────────────────────────────────
    print_summary(results)
    print_failure_report(results)
    print_footer()

    console.print(
        f"\n  [dim]Total wall time:[/dim] [cyan]{elapsed_total:.0f} ms[/cyan]\n"
    )

    # ── Save to disk ──────────────────────────────────────────────────────────
    if not args.no_save:
        save_results(results, args.output_dir)

    # ── Exit code ─────────────────────────────────────────────────────────────
    failed = sum(1 for r in results if not r.passed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
