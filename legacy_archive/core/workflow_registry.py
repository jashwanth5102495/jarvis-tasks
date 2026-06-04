"""
workflow_registry.py
====================
Reusable workflow template registry.

A WorkflowTemplate defines the canonical step sequence for a named
workflow. Templates are parameterised — they receive a Goal at
instantiation time and produce concrete WorkflowStep lists.

Built-in templates
------------------
  flask_api          : Full Flask REST API project pipeline
  portfolio_website  : Portfolio site with research + scaffold + assets
  python_script      : Single-file Python script with syntax check
  research_pipeline  : Web research → notes → summary
  automation_script  : Automation script with syntax verification
  design_brief       : Design brief + browser tool launch

Adding new templates
--------------------
  1. Define a function  _build_<name>(goal) → List[WorkflowStep]
  2. Register it in WORKFLOW_TEMPLATES dict at the bottom of this file
  3. Done — the orchestrator picks it up automatically
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Dict, List, Optional

from core.models import Goal
from orchestration.workflow_state import WorkflowStep
from skills.execution.execution_context import RiskLevel

logger = logging.getLogger(__name__)

# Type alias
TemplateBuilder = Callable[[Goal], List[WorkflowStep]]


def _slug(text: str) -> str:
    return re.sub(r"[^\w]+", "_", text.lower()).strip("_")[:40]


# ─────────────────────────────────────────────────────────────────────────────
# Template builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_flask_api(goal: Goal) -> List[WorkflowStep]:
    pname = _slug(goal.goal)
    s1 = WorkflowStep(
        name="Create project structure",
        executor="coding", action="generate_project_structure",
        params={"project_name": pname, "goal": goal.goal,
                "requirements": goal.requirements},
        risk_level=RiskLevel.LOW.value, stage="setup",
    )
    s2 = WorkflowStep(
        name="Write starter files",
        executor="coding", action="write_starter_files",
        params={"project_name": pname, "goal": goal.goal,
                "requirements": goal.requirements},
        risk_level=RiskLevel.LOW.value, stage="setup",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="Generate README",
        executor="file", action="create_file",
        params={"path": f"{pname}/README.md",
                "content": _readme_content(goal, pname)},
        risk_level=RiskLevel.LOW.value, stage="docs",
        depends_on=[s1.step_id],
    )
    s4 = WorkflowStep(
        name="Verify app.py syntax",
        executor="coding", action="verify_syntax",
        params={"script_path": f"{pname}/app.py"},
        risk_level=RiskLevel.MEDIUM.value, stage="verify",
        depends_on=[s2.step_id],
    )
    s5 = WorkflowStep(
        name="Log workflow completion",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[WORKFLOW] flask_api: {goal.goal}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
        depends_on=[s3.step_id, s4.step_id],
    )
    return [s1, s2, s3, s4, s5]


def _build_portfolio_website(goal: Goal) -> List[WorkflowStep]:
    pname = _slug(goal.goal)
    s1 = WorkflowStep(
        name="Research portfolio inspiration",
        executor="browser", action="search",
        params={"query": f"portfolio website inspiration {goal.goal}"},
        risk_level=RiskLevel.MEDIUM.value, stage="research",
    )
    s2 = WorkflowStep(
        name="Create project structure",
        executor="coding", action="generate_project_structure",
        params={"project_name": pname, "goal": goal.goal,
                "requirements": goal.requirements},
        risk_level=RiskLevel.LOW.value, stage="setup",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="Create assets folder",
        executor="file", action="create_dir",
        params={"path": f"{pname}/assets"},
        risk_level=RiskLevel.LOW.value, stage="setup",
        depends_on=[s2.step_id],
    )
    s4 = WorkflowStep(
        name="Create CSS folder",
        executor="file", action="create_dir",
        params={"path": f"{pname}/assets/css"},
        risk_level=RiskLevel.LOW.value, stage="setup",
        depends_on=[s3.step_id],
    )
    s5 = WorkflowStep(
        name="Generate index.html",
        executor="file", action="create_file",
        params={"path": f"{pname}/index.html",
                "content": _html_template(goal, pname)},
        risk_level=RiskLevel.LOW.value, stage="build",
        depends_on=[s2.step_id],
    )
    s6 = WorkflowStep(
        name="Generate style.css",
        executor="file", action="create_file",
        params={"path": f"{pname}/assets/css/style.css",
                "content": _css_template()},
        risk_level=RiskLevel.LOW.value, stage="build",
        depends_on=[s4.step_id],
    )
    s7 = WorkflowStep(
        name="Generate README",
        executor="file", action="create_file",
        params={"path": f"{pname}/README.md",
                "content": _readme_content(goal, pname)},
        risk_level=RiskLevel.LOW.value, stage="docs",
        depends_on=[s2.step_id],
    )
    s8 = WorkflowStep(
        name="Log workflow completion",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[WORKFLOW] portfolio_website: {goal.goal}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
        depends_on=[s5.step_id, s6.step_id, s7.step_id],
    )
    return [s1, s2, s3, s4, s5, s6, s7, s8]


def _build_python_script(goal: Goal) -> List[WorkflowStep]:
    pname  = _slug(goal.goal)
    script = f"{pname}.py"
    s1 = WorkflowStep(
        name="Generate Python script",
        executor="coding", action="generate_python_script",
        params={"project_name": "scripts", "script_name": script,
                "goal": goal.goal},
        risk_level=RiskLevel.LOW.value, stage="build",
    )
    s2 = WorkflowStep(
        name="Verify script syntax",
        executor="coding", action="verify_syntax",
        params={"script_path": f"scripts/{script}"},
        risk_level=RiskLevel.MEDIUM.value, stage="verify",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="Log completion",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[WORKFLOW] python_script: {goal.goal}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
        depends_on=[s2.step_id],
    )
    return [s1, s2, s3]


def _build_research_pipeline(goal: Goal) -> List[WorkflowStep]:
    query = goal.goal
    slug  = _slug(query)
    s1 = WorkflowStep(
        name="Web search",
        executor="browser", action="search",
        params={"query": query},
        risk_level=RiskLevel.MEDIUM.value, stage="research",
    )
    s2 = WorkflowStep(
        name="Create research notes file",
        executor="file", action="create_file",
        params={"path": f"research/{slug}_notes.md",
                "content": f"# Research: {query}\n\n## Query\n\n{query}\n\n## Notes\n\n"},
        risk_level=RiskLevel.LOW.value, stage="capture",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="Create research summary",
        executor="file", action="create_file",
        params={"path": f"research/{slug}_summary.md",
                "content": f"# Summary: {query}\n\n## Key Findings\n\n- (fill in)\n\n## Sources\n\n"},
        risk_level=RiskLevel.LOW.value, stage="capture",
        depends_on=[s1.step_id],
    )
    s4 = WorkflowStep(
        name="Log research workflow",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[WORKFLOW] research_pipeline: {query}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
        depends_on=[s2.step_id, s3.step_id],
    )
    return [s1, s2, s3, s4]


def _build_automation_script(goal: Goal) -> List[WorkflowStep]:
    pname  = _slug(goal.goal)
    script = f"automation/{pname}.py"
    s1 = WorkflowStep(
        name="Create automation script",
        executor="file", action="create_file",
        params={"path": script,
                "content": _automation_template(goal)},
        risk_level=RiskLevel.LOW.value, stage="build",
    )
    s2 = WorkflowStep(
        name="Verify script syntax",
        executor="coding", action="verify_syntax",
        params={"script_path": script},
        risk_level=RiskLevel.MEDIUM.value, stage="verify",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="Log completion",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[WORKFLOW] automation_script: {goal.goal}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
        depends_on=[s2.step_id],
    )
    return [s1, s2, s3]


def _build_design_brief(goal: Goal) -> List[WorkflowStep]:
    pname = _slug(goal.goal)
    reqs  = "\n".join(f"- {r}" for r in goal.requirements) or "- (none specified)"
    s1 = WorkflowStep(
        name="Create design brief",
        executor="file", action="create_file",
        params={"path": f"design/{pname}/brief.md",
                "content": (
                    f"# Design Brief: {goal.goal}\n\n"
                    f"## Requirements\n\n{reqs}\n\n"
                    f"## Style Notes\n\n- (add style notes)\n\n"
                    f"## Deliverables\n\n- Final design file\n- Export PNG/PDF\n"
                )},
        risk_level=RiskLevel.LOW.value, stage="setup",
    )
    s2 = WorkflowStep(
        name="Open design tool",
        executor="browser", action="open_url",
        params={"url": "https://www.canva.com"},
        risk_level=RiskLevel.MEDIUM.value, stage="execute",
        depends_on=[s1.step_id],
    )
    s3 = WorkflowStep(
        name="Log completion",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[WORKFLOW] design_brief: {goal.goal}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
        depends_on=[s1.step_id],
    )
    return [s1, s2, s3]


# ─────────────────────────────────────────────────────────────────────────────
# Content helpers
# ─────────────────────────────────────────────────────────────────────────────

def _readme_content(goal: Goal, pname: str) -> str:
    reqs = "\n".join(f"- {r}" for r in goal.requirements) or "- (none specified)"
    return (
        f"# {pname.replace('_', ' ').title()}\n\n"
        f"> {goal.goal}\n\n"
        f"## Requirements\n\n{reqs}\n\n"
        f"## Setup\n\n"
        f"```bash\npip install -r requirements.txt\npython main.py\n```\n\n"
        f"## Generated by\n\nJARVIS AI Operating System — Milestone 3\n"
    )


def _html_template(goal: Goal, pname: str) -> str:
    title = pname.replace("_", " ").title()
    return (
        f'<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        f'  <meta charset="UTF-8">\n'
        f'  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <title>{title}</title>\n'
        f'  <link rel="stylesheet" href="assets/css/style.css">\n'
        f'</head>\n<body>\n'
        f'  <header>\n    <h1>{title}</h1>\n    <nav></nav>\n  </header>\n'
        f'  <main>\n    <section id="about">\n      <h2>About</h2>\n'
        f'      <p>{goal.goal}</p>\n    </section>\n'
        f'    <section id="projects">\n      <h2>Projects</h2>\n    </section>\n'
        f'    <section id="contact">\n      <h2>Contact</h2>\n    </section>\n'
        f'  </main>\n  <footer><p>Generated by JARVIS</p></footer>\n</body>\n</html>\n'
    )


def _css_template() -> str:
    return (
        "* { box-sizing: border-box; margin: 0; padding: 0; }\n"
        "body { font-family: system-ui, sans-serif; line-height: 1.6; color: #333; }\n"
        "header { background: #1a1a2e; color: white; padding: 1rem 2rem; }\n"
        "main { max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }\n"
        "section { margin-bottom: 3rem; }\n"
        "h1, h2 { margin-bottom: 1rem; }\n"
        "footer { text-align: center; padding: 2rem; color: #666; }\n"
    )


def _automation_template(goal: Goal) -> str:
    return (
        f'"""\nAutomation: {goal.goal}\nGenerated by JARVIS.\n"""\n\n'
        f"import logging\nimport time\n\n"
        f"logging.basicConfig(level=logging.INFO)\n"
        f"logger = logging.getLogger(__name__)\n\n\n"
        f"def run():\n"
        f"    logger.info('Starting: {goal.goal}')\n"
        f"    # TODO: implement automation logic\n"
        f"    pass\n\n\n"
        f"if __name__ == '__main__':\n    run()\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Computer Control workflow templates (Milestone 4)
# ─────────────────────────────────────────────────────────────────────────────

def _build_open_chrome_search(goal: Goal) -> List[WorkflowStep]:
    query = goal.goal
    s1 = WorkflowStep(
        name="Log computer control intent",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[CC_WORKFLOW] open_chrome_search: {query}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
    )
    return [s1]   # Actual desktop steps run via ControlManager


def _build_open_app(goal: Goal) -> List[WorkflowStep]:
    s1 = WorkflowStep(
        name="Log app launch intent",
        executor="file", action="append_file",
        params={"path": "logs/workflows.log",
                "content": f"[CC_WORKFLOW] open_app: {goal.goal}\n"},
        risk_level=RiskLevel.LOW.value, stage="log",
    )
    return [s1]


# Maps workflow name → builder function
WORKFLOW_TEMPLATES: Dict[str, TemplateBuilder] = {
    "flask_api":           _build_flask_api,
    "portfolio_website":   _build_portfolio_website,
    "python_script":       _build_python_script,
    "research_pipeline":   _build_research_pipeline,
    "automation_script":   _build_automation_script,
    "design_brief":        _build_design_brief,
    "open_chrome_search":  _build_open_chrome_search,
    "open_app":            _build_open_app,
}

# Maps Goal category → default workflow template name
CATEGORY_TO_WORKFLOW: Dict[str, str] = {
    "software_development": "flask_api",
    "design":               "design_brief",
    "research":             "research_pipeline",
    "automation":           "automation_script",
    "communication":        "python_script",
    "system_operations":    "python_script",
    "productivity":         "python_script",
    "business":             "python_script",
}


class WorkflowRegistry:
    """
    Resolves a Goal to a concrete list of WorkflowSteps.

    Resolution order
    ----------------
    1. Exact template name match (if goal text contains a known template name)
    2. Category → default template mapping
    3. Fallback: generic file-creation step
    """

    def resolve(self, goal: Goal) -> tuple[str, List[WorkflowStep]]:
        """
        Returns (workflow_name, steps).
        """
        # 1. Check if goal text hints at a specific template
        goal_lower = goal.goal.lower()
        for tname in WORKFLOW_TEMPLATES:
            if tname.replace("_", " ") in goal_lower or tname in goal_lower:
                return tname, WORKFLOW_TEMPLATES[tname](goal)

        # 2. Category mapping
        tname = CATEGORY_TO_WORKFLOW.get(goal.category)
        if tname and tname in WORKFLOW_TEMPLATES:
            # Refine: if goal mentions "portfolio", use portfolio template
            if "portfolio" in goal_lower and goal.category == "software_development":
                return "portfolio_website", WORKFLOW_TEMPLATES["portfolio_website"](goal)
            return tname, WORKFLOW_TEMPLATES[tname](goal)

        # 3. Fallback
        logger.warning(
            f"WorkflowRegistry: no template for category={goal.category!r}, "
            f"using generic fallback"
        )
        return "generic", self._generic_fallback(goal)

    def get_template(self, name: str, goal: Goal) -> List[WorkflowStep]:
        """Directly instantiate a named template."""
        if name not in WORKFLOW_TEMPLATES:
            raise KeyError(f"Unknown workflow template: {name!r}")
        return WORKFLOW_TEMPLATES[name](goal)

    def list_templates(self) -> List[str]:
        return list(WORKFLOW_TEMPLATES.keys())

    @staticmethod
    def _generic_fallback(goal: Goal) -> List[WorkflowStep]:
        slug = _slug(goal.goal)
        return [
            WorkflowStep(
                name="Create task notes",
                executor="file", action="create_file",
                params={"path": f"notes/{slug}.md",
                        "content": f"# {goal.goal}\n\n"},
                risk_level=RiskLevel.LOW.value, stage="main",
            )
        ]


# Module-level singleton
workflow_registry = WorkflowRegistry()
