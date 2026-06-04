"""
validators.py
=============
Pure validation logic — no I/O, no rich, no side-effects.
Each validator returns a TestResult dataclass.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Result model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    """Outcome of a single assertion within a test case."""
    name: str
    passed: bool
    expected: Any
    actual: Any
    detail: str = ""


@dataclass
class TestResult:
    """Aggregated outcome for one test case."""
    index: int
    input_text: str
    expected_category: str
    actual_category: Optional[str]
    confidence: Optional[float]
    requirements: List[str]
    checks: List[CheckResult] = field(default_factory=list)
    error: Optional[str] = None          # set when an exception was raised
    rejected: bool = False               # True when ValueError was raised
    elapsed_ms: float = 0.0
    tags: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        if self.error and not self.rejected:
            return False
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> List[CheckResult]:
        return [c for c in self.checks if not c.passed]


# ─────────────────────────────────────────────────────────────────────────────
# Validator
# ─────────────────────────────────────────────────────────────────────────────

class TestValidator:
    """Runs a single test case against the Brain and returns a TestResult."""

    def __init__(self, brain_instance):
        self._brain = brain_instance

    def run(self, case: Dict, index: int) -> TestResult:
        input_text      = case["input"]
        expected_cat    = case["expected_category"]
        min_conf        = case.get("min_confidence", 0)
        expected_reqs   = [r.lower() for r in case.get("expected_reqs", [])]
        should_reject   = case.get("should_reject", False)
        tags            = case.get("tags", [])

        result = TestResult(
            index=index,
            input_text=input_text,
            expected_category=expected_cat,
            actual_category=None,
            confidence=None,
            requirements=[],
            tags=tags,
        )

        t0 = time.perf_counter()

        try:
            goal = self._brain.analyze_task(input_text)
            result.actual_category = goal.category
            result.confidence      = goal.confidence
            result.requirements    = goal.requirements

        except ValueError as exc:
            result.rejected = True
            result.error    = str(exc)
            result.elapsed_ms = (time.perf_counter() - t0) * 1000

            # For should_reject cases a ValueError is the CORRECT outcome
            result.checks.append(CheckResult(
                name="rejection",
                passed=should_reject,
                expected="ValueError raised" if should_reject else "no error",
                actual="ValueError raised",
                detail=str(exc),
            ))
            return result

        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
            result.elapsed_ms = (time.perf_counter() - t0) * 1000
            result.checks.append(CheckResult(
                name="no_crash",
                passed=False,
                expected="no exception",
                actual=result.error,
            ))
            return result

        result.elapsed_ms = (time.perf_counter() - t0) * 1000

        # ── Check 1: should NOT have been rejected ────────────────────────
        if should_reject:
            result.checks.append(CheckResult(
                name="rejection",
                passed=False,
                expected="ValueError raised",
                actual=f"category={result.actual_category}",
                detail="Input should have been rejected but was classified",
            ))
            return result

        # ── Check 2: category match ───────────────────────────────────────
        cat_match = result.actual_category == expected_cat
        result.checks.append(CheckResult(
            name="category",
            passed=cat_match,
            expected=expected_cat,
            actual=result.actual_category,
        ))

        # ── Check 3: confidence threshold ────────────────────────────────
        if min_conf > 0:
            conf_ok = (result.confidence is not None
                       and result.confidence >= min_conf)
            result.checks.append(CheckResult(
                name="confidence",
                passed=conf_ok,
                expected=f">= {min_conf}%",
                actual=f"{result.confidence}%",
            ))

        # ── Check 4: confidence never 100 % ──────────────────────────────
        if result.confidence is not None and expected_cat != "internal_commands":
            result.checks.append(CheckResult(
                name="confidence_cap",
                passed=result.confidence < 100.0,
                expected="< 100%",
                actual=f"{result.confidence}%",
            ))

        # ── Check 5: required requirements present ────────────────────────
        if expected_reqs:
            extracted_lower = [r.lower() for r in result.requirements]
            for req in expected_reqs:
                found = any(req in ext for ext in extracted_lower)
                result.checks.append(CheckResult(
                    name=f"req:{req}",
                    passed=found,
                    expected=f'"{req}" in requirements',
                    actual=str(result.requirements),
                ))

        return result
