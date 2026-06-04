
"""
prompt_engine.py
================
Engine for generating structured prompts for LLMs.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Engine for constructing LLM prompts with structured templates.
    """

    # System prompts
    SYSTEM_PROMPT_REASONING = """
You are JARVIS, a helpful AI assistant operating within the JARVIS AI OS.
Your role is to assist with workflow planning, task reasoning, and orchestration.
You operate with:
- Think carefully about workflows
- Suggest safe, executable plans
- Reference past context
- Follow safety and enforce safety
- Provide clear, structured responses
- Work within JARVIS's capabilities.

IMPORTANT: You do NOT execute any code execution directly.
You generate plans and workflows that validated by JARVIS's safety systems.
"""

    SYSTEM_PROMPT_CODING = """
You are JARVIS Code Assistant, a coding-specialized AI.
You help with:
- Code generation
- Workflow design for coding tasks
- Debugging suggestions
- Best practices
- Architecture recommendations

Always:
- Use safety (never produce malicious code
- Follow best practices
- Use the existing JARVIS architecture
"""

    SYSTEM_PROMPT_PLANNING = """
You are JARVIS Planning Assistant. Your job:
Take a goal and generate a structured, executable workflow plan.

Workflow format:
- Use JARVIS's capabilities
- Plan executable
- Safe, step-by-step
- Use existing skills
- Safe
- Safe

Output as JSON only.

Example output:
{
  "steps": [
    {
      "action": "...",
      "params": "..."
    }
  ]
}
"""

    def generate_prompt(
        self,
        purpose: str,
        context: Optional[Dict[str, Any]] = None,
        instructions: Optional[str] = None,
    ) -> str:
        """
        Generate a complete prompt for a specific purpose.
        """
        system_prompt = self._get_system_prompt(purpose)
        context_section = self._format_context(context) if context else ""
        instruction_section = instructions or ""

        prompt = f"{system_prompt}\n\n{context_section}\n\n{instruction_section}"
        return prompt.strip()

    def _get_system_prompt(self, purpose: str) -> str:
        """Get the appropriate system prompt for a purpose."""
        if purpose == "coding":
            return self.SYSTEM_PROMPT_CODING
        elif purpose == "planning":
            return self.SYSTEM_PROMPT_PLANNING
        else:
            return self.SYSTEM_PROMPT_REASONING

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into a readable string."""
        parts = ["## Context\n"]
        for key, value in context.items():
            parts.append(f"- {key}:\n  {value}")
        return "\n".join(parts)


# Module-level singleton
prompt_engine = PromptEngine()

