"""
task_router.py
==============
Maps a Goal category to the primary executor and generates
a list of ExecutionStep descriptors that the ExecutionManager
will process one-by-one.

An ExecutionStep is a lightweight dict:
  {
    "description": str,      # human-readable label shown in the plan
    "executor":    str,      # key in EXECUTORS registry
    "action":      str,      # method name on the executor
    "params":      dict,     # forwarded to the executor
    "risk_level":  RiskLevel # used by PermissionManager
  }

The router does NOT execute anything — it only plans.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from core.models import Goal
from skills.execution.execution_context import RiskLevel

logger = logging.getLogger(__name__)

ExecutionStep = Dict[str, Any]


class TaskRouter:
    """
    Translates a classified Goal into a concrete list of ExecutionSteps.

    Each category has a dedicated _route_<category> method so new
    categories can be added without touching the dispatch logic.
    """

    def route(self, goal: Goal) -> List[ExecutionStep]:
        category = goal.category.lower()
        method   = getattr(self, f"_route_{category}", self._route_general)
        steps    = method(goal)
        logger.info(
            f"TaskRouter: {len(steps)} step(s) planned "
            f"for category={category!r}"
        )
        return steps

    # ── Category routers ───────────────────────────────────────────────────────

    def _route_software_development(self, goal: Goal) -> List[ExecutionStep]:
        project_name = self._slug(goal.goal)
        return [
            {
                "description": f"Create project folder '{project_name}'",
                "executor":    "coding",
                "action":      "generate_project_structure",
                "params":      {"project_name": project_name, "goal": goal.goal,
                                "requirements": goal.requirements},
                "risk_level":  RiskLevel.LOW,
            },
            {
                "description": "Write starter code files",
                "executor":    "coding",
                "action":      "write_starter_files",
                "params":      {"project_name": project_name, "goal": goal.goal,
                                "requirements": goal.requirements},
                "risk_level":  RiskLevel.LOW,
            },
            {
                "description": "Generate README.md",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"{project_name}/README.md",
                    "content": self._readme(goal),
                },
                "risk_level":  RiskLevel.LOW,
            },
        ]

    def _route_design(self, goal: Goal) -> List[ExecutionStep]:
        project_name = self._slug(goal.goal)
        return [
            {
                "description": f"Create design brief file for '{goal.goal}'",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"design/{project_name}/brief.md",
                    "content": self._design_brief(goal),
                },
                "risk_level":  RiskLevel.LOW,
            },
            {
                "description": "Open design tool in browser",
                "executor":    "browser",
                "action":      "open_url",
                "params":      {"url": "https://www.canva.com"},
                "risk_level":  RiskLevel.MEDIUM,
            },
        ]

    def _route_research(self, goal: Goal) -> List[ExecutionStep]:
        query = goal.goal
        return [
            {
                "description": f"Search the web for: {query}",
                "executor":    "browser",
                "action":      "search",
                "params":      {"query": query},
                "risk_level":  RiskLevel.MEDIUM,
            },
            {
                "description": "Save research notes",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"research/{self._slug(query)}_notes.md",
                    "content": f"# Research: {query}\n\n## Notes\n\n",
                },
                "risk_level":  RiskLevel.LOW,
            },
        ]

    def _route_system_operations(self, goal: Goal) -> List[ExecutionStep]:
        return [
            {
                "description": f"Execute system operation: {goal.goal}",
                "executor":    "terminal",
                "action":      "run_safe_command",
                "params":      {"command": self._system_command(goal)},
                "risk_level":  RiskLevel.HIGH,
            },
            {
                "description": "Log operation result",
                "executor":    "file",
                "action":      "append_file",
                "params":      {
                    "path":    "logs/operations.log",
                    "content": f"[OPERATION] {goal.goal}\n",
                },
                "risk_level":  RiskLevel.LOW,
            },
        ]

    def _route_communication(self, goal: Goal) -> List[ExecutionStep]:
        project_name = self._slug(goal.goal)
        return [
            {
                "description": f"Draft communication: {goal.goal}",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"communications/{project_name}.md",
                    "content": self._comm_draft(goal),
                },
                "risk_level":  RiskLevel.LOW,
            },
        ]

    def _route_automation(self, goal: Goal) -> List[ExecutionStep]:
        project_name = self._slug(goal.goal)
        return [
            {
                "description": "Create automation script",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"automation/{project_name}.py",
                    "content": self._automation_template(goal),
                },
                "risk_level":  RiskLevel.LOW,
            },
            {
                "description": "Verify script syntax",
                "executor":    "terminal",
                "action":      "run_safe_command",
                "params":      {"command": f"python -m py_compile automation/{project_name}.py"},
                "risk_level":  RiskLevel.MEDIUM,
            },
        ]

    def _route_productivity(self, goal: Goal) -> List[ExecutionStep]:
        project_name = self._slug(goal.goal)
        return [
            {
                "description": "Create task list",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"productivity/{project_name}.md",
                    "content": f"# {goal.goal}\n\n## Tasks\n\n- [ ] Task 1\n- [ ] Task 2\n",
                },
                "risk_level":  RiskLevel.LOW,
            },
        ]

    def _route_business(self, goal: Goal) -> List[ExecutionStep]:
        project_name = self._slug(goal.goal)
        return [
            {
                "description": "Create business document",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"business/{project_name}.md",
                    "content": f"# {goal.goal}\n\n## Overview\n\n",
                },
                "risk_level":  RiskLevel.LOW,
            },
        ]

    def _route_text_to_speech(self, goal: Goal) -> List[ExecutionStep]:
        from brain.voice_workflow_generator import voice_workflow_generator
        steps: List[ExecutionStep] = []
        voice_actions = voice_workflow_generator.generate_from_input(
            goal.goal,
            goal.category,
            goal.requirements
        )
        for action in voice_actions:
            steps.append({
                "description": action.description,
                "executor":    "voice",
                "action":      action.action_type,
                "params":      action.params,
                "risk_level":  RiskLevel.LOW,
            })
        return steps

    def _route_speech_control(self, goal: Goal) -> List[ExecutionStep]:
        from brain.voice_workflow_generator import voice_workflow_generator
        steps: List[ExecutionStep] = []
        voice_actions = voice_workflow_generator.generate_from_input(
            goal.goal,
            goal.category,
            goal.requirements
        )
        for action in voice_actions:
            steps.append({
                "description": action.description,
                "executor":    "voice",
                "action":      action.action_type,
                "params":      action.params,
                "risk_level":  RiskLevel.LOW,
            })
        return steps

    def _route_voice_interaction(self, goal: Goal) -> List[ExecutionStep]:
        from brain.voice_workflow_generator import voice_workflow_generator
        steps: List[ExecutionStep] = []
        voice_actions = voice_workflow_generator.generate_from_input(
            goal.goal,
            goal.category,
            goal.requirements
        )
        for action in voice_actions:
            steps.append({
                "description": action.description,
                "executor":    "voice",
                "action":      action.action_type,
                "params":      action.params,
                "risk_level":  RiskLevel.MEDIUM,
            })
        return steps

    def _route_general(self, goal: Goal) -> List[ExecutionStep]:
        return [
            {
                "description": f"Create notes for: {goal.goal}",
                "executor":    "file",
                "action":      "create_file",
                "params":      {
                    "path":    f"notes/{self._slug(goal.goal)}.md",
                    "content": f"# {goal.goal}\n\n",
                },
                "risk_level":  RiskLevel.LOW,
            },
        ]

    # ── Content generators ─────────────────────────────────────────────────────

    @staticmethod
    def _slug(text: str) -> str:
        import re
        return re.sub(r"[^\w]+", "_", text.lower()).strip("_")[:40]

    @staticmethod
    def _readme(goal: Goal) -> str:
        reqs = "\n".join(f"- {r}" for r in goal.requirements) or "- (none specified)"
        return (
            f"# {goal.goal}\n\n"
            f"## Overview\n\n"
            f"Auto-generated by JARVIS.\n\n"
            f"## Requirements\n\n{reqs}\n\n"
            f"## Getting Started\n\n"
            f"```bash\n# Install dependencies\npip install -r requirements.txt\n\n"
            f"# Run the project\npython main.py\n```\n"
        )

    @staticmethod
    def _design_brief(goal: Goal) -> str:
        reqs = "\n".join(f"- {r}" for r in goal.requirements) or "- (none specified)"
        return (
            f"# Design Brief: {goal.goal}\n\n"
            f"## Requirements\n\n{reqs}\n\n"
            f"## Style Notes\n\n- (add style notes here)\n\n"
            f"## Deliverables\n\n- Final design file\n- Export in PNG/PDF\n"
        )

    @staticmethod
    def _comm_draft(goal: Goal) -> str:
        return (
            f"# Communication Draft\n\n"
            f"**Task:** {goal.goal}\n\n"
            f"---\n\n"
            f"Subject: \n\nDear [Recipient],\n\n[Body]\n\nBest regards,\n[Your Name]\n"
        )

    @staticmethod
    def _automation_template(goal: Goal) -> str:
        return (
            f'"""\nAutomation script: {goal.goal}\nGenerated by JARVIS.\n"""\n\n'
            f"import time\nimport logging\n\n"
            f"logging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n\n\n"
            f"def run():\n"
            f"    logger.info('Starting automation: {goal.goal}')\n"
            f"    # TODO: implement automation logic\n"
            f"    pass\n\n\n"
            f"if __name__ == '__main__':\n    run()\n"
        )

    @staticmethod
    def _system_command(goal: Goal) -> str:
        """Map common system operation goals to safe shell commands."""
        g = goal.goal.lower()
        if "disk" in g or "cleanup" in g or "temporary" in g:
            return "echo Disk cleanup simulation — no files deleted"
        if "backup" in g:
            return "echo Backup simulation — no files copied"
        if "monitor" in g or "log" in g:
            return "echo Log monitoring simulation"
        if "restart" in g or "reboot" in g:
            return "echo Restart simulation — system not restarted"
        return f"echo System operation: {goal.goal}"


# Module-level singleton
task_router = TaskRouter()
