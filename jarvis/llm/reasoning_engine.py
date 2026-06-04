
"""
reasoning_engine.py
===================
Hybrid reasoning engine combining rule-based and LLM-based reasoning.
"""

from __future__ import annotations

import logging
import json
from typing import Dict, Any, Optional, List

from jarvis.llm.llm_manager import llm_manager
from jarvis.llm.prompt_engine import prompt_engine
from jarvis.llm.context_builder import context_builder
from jarvis.llm.semantic_retriever import semantic_retriever
from jarvis.llm.response_validator import response_validator

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Hybrid reasoning engine combining rule-based and LLM reasoning.
    """

    def __init__(self):
        self._use_llm = True  # Can toggle for debugging

    def plan_workflow(
        self,
        goal: str,
        use_llm: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Plan a workflow for a given goal.
        """
        use_llm = use_llm if use_llm is not None else self._use_llm

        if not use_llm:
            return self._plan_rule_based(goal)

        return self._plan_llm_based(goal)

    def _plan_rule_based(self, goal: str) -> Dict[str, Any]:
        """Fallback rule-based planning."""
        logger.info("Using rule-based planning")
        # Return a simple plan
        return {
            "goal": goal,
            "steps": [{"action": "research", "params": {"query": goal}}],
            "notes": "Rule-based fallback plan",
        }

    def _plan_llm_based(self, goal: str) -> Dict[str, Any]:
        """LLM-based intelligent planning."""
        logger.info("Using LLM-based planning")

        # Build context
        context = context_builder.build_context(goal)
        semantic_context = semantic_retriever.retrieve_all(goal)

        # Generate prompt
        prompt = prompt_engine.generate_prompt(
            purpose="planning",
            context={**context, **semantic_context},
            instructions=f"Generate a workflow plan for this goal: {goal}",
        )

        # Get LLM response
        try:
            response = llm_manager.generate(
                prompt=prompt,
                purpose="reasoning",
                system_prompt=prompt_engine.SYSTEM_PROMPT_PLANNING,
            )

            # Validate response
            response_validator.validate(
                response,
                expected_schema={"type": "object", "required": ["steps"]},
                require_safe=True,
            )

            # Parse response
            try:
                plan = json.loads(response)
                return plan
            except json.JSONDecodeError:
                # If JSON fails, try to extract a plan
                logger.warning("LLM didn't return valid JSON, using fallback")
                return self._plan_rule_based(goal)

        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            return self._plan_rule_based(goal)

    def reason_about_error(
        self, error: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Reason about an error and suggest fixes.
        """
        prompt = prompt_engine.generate_prompt(
            purpose="reasoning",
            context=context,
            instructions=f"Analyze this error and suggest a fix:\n{error}",
        )

        try:
            response = llm_manager.generate(prompt, purpose="reasoning")
            response_validator.validate(response, require_safe=True)
            return response
        except Exception as e:
            logger.error(f"Error reasoning failed: {e}")
            return f"Error analysis unavailable: {str(e)}"


# Module-level singleton
reasoning_engine = ReasoningEngine()

