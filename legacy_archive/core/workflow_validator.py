"""
workflow_validator.py
=====================
Pre-execution validation of a workflow step list.

Checks
------
1. All step_ids are unique
2. All dependency references resolve to existing step_ids
3. No circular dependencies
4. All executor names are registered
5. All action names are supported by their executor
6. Required params are present for each action

Returns a ValidationReport with a list of errors and warnings.
A workflow with errors must NOT be executed.
A workflow with only warnings may proceed with user acknowledgement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from orchestration.dependency_manager import DependencyManager
from orchestration.workflow_state import WorkflowStep

logger = logging.getLogger(__name__)

# Required params per executor+action
_REQUIRED_PARAMS: Dict[str, List[str]] = {
    "file:create_file":   ["path"],
    "file:read_file":     ["path"],
    "file:write_file":    ["path"],
    "file:append_file":   ["path"],
    "file:delete_file":   ["path"],
    "file:rename_file":   ["path", "new_path"],
    "file:create_dir":    ["path"],
    "browser:open_url":   ["url"],
    "browser:search":     ["query"],
    "browser:fetch_page": ["url"],
    "terminal:run_safe_command":  ["command"],
    "terminal:install_package":   ["package"],
    "terminal:run_python_script": ["script_path"],
    "coding:verify_syntax":       ["script_path"],
    "coding:generate_project_structure": ["project_name"],
    "coding:write_starter_files":        ["project_name"],
    "coding:generate_python_script":     ["script_name"],
}


@dataclass
class ValidationReport:
    errors:   List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(f"  ERROR   : {e}")
        for w in self.warnings:
            lines.append(f"  WARNING : {w}")
        return "\n".join(lines) if lines else "  OK — no issues found"


class WorkflowValidator:
    """
    Validates a list of WorkflowSteps before execution.

    Usage
    -----
    report = WorkflowValidator(registered_executors).validate(steps)
    if not report.is_valid:
        print(report)
    """

    def __init__(self, registered_executors: Dict[str, Any]):
        self._executors = registered_executors

    def validate(self, steps: List[WorkflowStep]) -> ValidationReport:
        report = ValidationReport()

        if not steps:
            report.warnings.append("Workflow has no steps.")
            return report

        # 1. Unique step IDs
        seen_ids: Set[str] = set()
        for step in steps:
            if step.step_id in seen_ids:
                report.errors.append(
                    f"Duplicate step_id {step.step_id!r} on step '{step.name}'"
                )
            seen_ids.add(step.step_id)

        # 2. Dependency graph validity
        dep_errors = DependencyManager.validate(steps)
        report.errors.extend(dep_errors)

        # 3. Executor registration
        for step in steps:
            if step.executor not in self._executors:
                report.errors.append(
                    f"Step '{step.name}': executor {step.executor!r} is not registered. "
                    f"Available: {list(self._executors.keys())}"
                )
                continue

            # 4. Action support
            executor = self._executors[step.executor]
            if hasattr(executor, "SUPPORTED_ACTIONS"):
                if step.action not in executor.SUPPORTED_ACTIONS:
                    report.errors.append(
                        f"Step '{step.name}': action {step.action!r} not supported "
                        f"by {step.executor!r}. "
                        f"Supported: {executor.SUPPORTED_ACTIONS}"
                    )

        # 5. Required params
        for step in steps:
            key = f"{step.executor}:{step.action}"
            required = _REQUIRED_PARAMS.get(key, [])
            for param in required:
                if param not in step.params:
                    report.errors.append(
                        f"Step '{step.name}': missing required param {param!r} "
                        f"for {step.executor}.{step.action}"
                    )

        # 6. Warn about HIGH risk steps
        for step in steps:
            if step.risk_level in ("high", "critical"):
                report.warnings.append(
                    f"Step '{step.name}' has {step.risk_level.upper()} risk — "
                    f"user confirmation will be required."
                )

        logger.info(
            f"WorkflowValidator: {len(report.errors)} errors, "
            f"{len(report.warnings)} warnings for {len(steps)} steps"
        )
        return report
