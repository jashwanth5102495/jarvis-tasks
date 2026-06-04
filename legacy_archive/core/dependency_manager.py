"""
dependency_manager.py
=====================
Dependency-aware execution ordering.

Builds a DAG (directed acyclic graph) from WorkflowStep.depends_on
declarations and produces a topologically-sorted execution order.

Features
--------
- Topological sort (Kahn's algorithm — O(V+E))
- Cycle detection with clear error messages
- Dependency satisfaction checking at runtime
- Blocked-step detection when a dependency failed/was denied

Usage
-----
order = DependencyManager.resolve_order(steps)
ready = DependencyManager.get_ready_steps(steps, completed_ids)
blocked = DependencyManager.get_blocked_steps(steps, failed_ids)
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Dict, List, Set

from orchestration.workflow_state import WorkflowStep, StepStatus

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Raised when the dependency graph is invalid (cycle, missing step, etc.)."""


class DependencyManager:
    """
    Static utility class — no instance state needed.
    All methods are class methods for easy use without instantiation.
    """

    @classmethod
    def resolve_order(cls, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """
        Return steps in topologically-sorted execution order.
        Raises DependencyError if a cycle is detected or a dependency
        references a non-existent step_id.
        """
        if not steps:
            return []

        id_to_step: Dict[str, WorkflowStep] = {s.step_id: s for s in steps}

        # Validate all dependency references exist
        for step in steps:
            for dep_id in step.depends_on:
                if dep_id not in id_to_step:
                    raise DependencyError(
                        f"Step {step.name!r} depends on unknown step_id {dep_id!r}"
                    )

        # Build adjacency list and in-degree map
        in_degree: Dict[str, int]        = {s.step_id: 0 for s in steps}
        dependents: Dict[str, List[str]] = defaultdict(list)  # dep → [steps that need it]

        for step in steps:
            for dep_id in step.depends_on:
                dependents[dep_id].append(step.step_id)
                in_degree[step.step_id] += 1

        # Kahn's algorithm
        queue: deque[str] = deque(
            sid for sid, deg in in_degree.items() if deg == 0
        )
        sorted_ids: List[str] = []

        while queue:
            sid = queue.popleft()
            sorted_ids.append(sid)
            for dependent_id in dependents[sid]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        if len(sorted_ids) != len(steps):
            # Find the cycle members for a helpful error message
            cycle_members = [
                id_to_step[sid].name
                for sid in in_degree
                if in_degree[sid] > 0
            ]
            raise DependencyError(
                f"Circular dependency detected among steps: {cycle_members}"
            )

        ordered = [id_to_step[sid] for sid in sorted_ids]
        logger.debug(
            f"DependencyManager: resolved order → "
            f"{[s.name for s in ordered]}"
        )
        return ordered

    @classmethod
    def get_ready_steps(
        cls,
        steps: List[WorkflowStep],
        completed_ids: Set[str],
    ) -> List[WorkflowStep]:
        """
        Return steps whose dependencies are all in completed_ids
        and whose own status is PENDING.
        """
        ready = []
        for step in steps:
            if step.status != StepStatus.PENDING:
                continue
            if all(dep in completed_ids for dep in step.depends_on):
                ready.append(step)
        return ready

    @classmethod
    def get_blocked_steps(
        cls,
        steps: List[WorkflowStep],
        failed_or_denied_ids: Set[str],
    ) -> List[WorkflowStep]:
        """
        Return PENDING steps that can never run because at least one
        of their dependencies has failed or been denied.
        """
        blocked = []
        for step in steps:
            if step.status != StepStatus.PENDING:
                continue
            if any(dep in failed_or_denied_ids for dep in step.depends_on):
                blocked.append(step)
        return blocked

    @classmethod
    def validate(cls, steps: List[WorkflowStep]) -> List[str]:
        """
        Validate the dependency graph without executing.
        Returns a list of error strings (empty = valid).
        """
        errors: List[str] = []
        id_to_step = {s.step_id: s for s in steps}

        for step in steps:
            for dep_id in step.depends_on:
                if dep_id not in id_to_step:
                    errors.append(
                        f"Step '{step.name}' references unknown dependency '{dep_id}'"
                    )

        try:
            cls.resolve_order(steps)
        except DependencyError as exc:
            errors.append(str(exc))

        return errors
