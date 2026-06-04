"""
stress_tests.py
===============
Rapid-fire stress testing utilities.
Runs all stress cases concurrently (thread-pool) and measures throughput.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from rich.console import Console

from tests.test_cases import STRESS_CASES
from tests.validators import TestValidator, TestResult

console = Console()


def run_stress_test(
    brain_instance,
    workers: int = 4,
    repeat: int = 1,
) -> List[TestResult]:
    """
    Execute all STRESS_CASES `repeat` times using a thread pool.

    Parameters
    ----------
    brain_instance : Brain
        Shared Brain instance (Brain is stateless per-call except debug toggle).
    workers : int
        Thread-pool size.
    repeat : int
        How many times to repeat the full stress suite.

    Returns
    -------
    List[TestResult]
    """
    validator = TestValidator(brain_instance)
    cases = STRESS_CASES * repeat

    results: List[TestResult] = [None] * len(cases)  # type: ignore
    t_start = time.perf_counter()

    console.print(
        f"\n  [bold cyan]Stress test:[/bold cyan] "
        f"{len(cases)} cases × {workers} workers"
    )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(validator.run, case, idx + 1): idx
            for idx, case in enumerate(cases)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                from tests.validators import TestResult, CheckResult
                r = TestResult(
                    index=idx + 1,
                    input_text=cases[idx]["input"],
                    expected_category=cases[idx]["expected_category"],
                    actual_category=None,
                    confidence=None,
                    requirements=[],
                    error=str(exc),
                )
                r.checks.append(CheckResult(
                    name="no_crash",
                    passed=False,
                    expected="no exception",
                    actual=str(exc),
                ))
                results[idx] = r

    elapsed = (time.perf_counter() - t_start) * 1000
    passed  = sum(1 for r in results if r and r.passed)
    total   = len(results)

    console.print(
        f"  Completed {total} stress cases in [cyan]{elapsed:.0f} ms[/cyan]  "
        f"([green]{passed}[/green] passed, "
        f"[red]{total - passed}[/red] failed)  "
        f"throughput: [cyan]{total / (elapsed / 1000):.0f} req/s[/cyan]"
    )

    return [r for r in results if r is not None]
