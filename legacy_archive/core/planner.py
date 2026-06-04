"""
planner.py
==========
Planner — translates a classified Goal into a human-readable Plan
(list of step descriptions) AND an executor-aware step list.

The Plan.steps list is used for display in the console.
The executor steps are consumed by the ExecutionManager.
"""

import logging
from core.models import Goal, Plan

logger = logging.getLogger(__name__)


class Planner:
    def __init__(self):
        pass

    def create_plan(self, goal: Goal) -> Plan:
        logger.info(
            f"Creating plan for goal: {goal.goal!r}, category: {goal.category}"
        )

        category = goal.category.lower()

        step_map = {
            "design": [
                "Understand design requirements",
                "Create design brief",
                "Open design tool",
                "Generate design assets",
                "Export and review",
            ],
            "software_development": [
                "Analyse requirements",
                "Generate project structure",
                "Write starter code files",
                "Create README and documentation",
                "Verify syntax and run tests",
            ],
            "research": [
                "Define research question",
                "Search the web for information",
                "Fetch and read relevant pages",
                "Synthesise findings",
                "Save research notes",
            ],
            "automation": [
                "Identify repetitive task",
                "Generate automation script",
                "Verify script syntax",
                "Test automation",
                "Deploy and monitor",
            ],
            "communication": [
                "Define communication goal",
                "Draft message content",
                "Review and edit draft",
                "Save draft to file",
                "Send via appropriate channel",
            ],
            "system_operations": [
                "Assess system requirements",
                "Prepare environment",
                "Execute system operation",
                "Verify completion",
                "Log operation result",
            ],
            "computer_control": [
                "Analyse control request",
                "Generate control workflow",
                "Request user permission",
                "Execute workflow actions",
                "Verify and log completion",
            ],
            "productivity": [
                "Define productivity goal",
                "Create task list",
                "Prioritise work",
                "Execute tasks",
                "Review progress",
            ],
            "business": [
                "Define business objective",
                "Analyse current state",
                "Create business document",
                "Review and refine",
                "Execute plan",
            ],
            "internal_commands": [
                "Process internal command",
            ],
            "text_to_speech": [
                "Analyse speech request",
                "Generate speech audio",
                "Play audio output",
            ],
            "speech_control": [
                "Analyse speech control request",
                "Execute voice control action",
            ],
            "voice_interaction": [
                "Activate voice mode",
                "Listen for user speech",
                "Process and respond to user",
            ],
        }

        steps = step_map.get(
            category,
            [
                "Understand the request",
                "Plan the approach",
                "Execute the task",
                "Verify completion",
            ],
        )

        plan = Plan(steps=steps)
        logger.info(f"Plan created with {len(steps)} steps")
        return plan


planner = Planner()
