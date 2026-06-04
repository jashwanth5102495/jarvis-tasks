
"""
learning_pipeline.py
===================
Processes research/knowledge into actionable learning plans.
Infers new capabilities, identifies missing executors, proposes integrations.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List
from dataclasses import dataclass, field

from evolution.knowledge_extractor import ExtractedKnowledge

logger = logging.getLogger(__name__)


@dataclass
class LearningPlan:
    """Plan for learning a new capability."""
    topic: str
    required_executors: List[str] = field(default_factory=list)
    new_skills: List[Dict[str, Any]] = field(default_factory=list)
    workflow_templates: List[Dict[str, Any]] = field(default_factory=list)
    integration_points: List[Dict[str, Any]] = field(default_factory=list)
    estimated_complexity: int = 1  # 1-5 scale


class LearningPipeline:
    """
    Pipeline that processes extracted knowledge into learning plans.
    """

    def __init__(self):
        pass

    def create_plan(self, knowledge: ExtractedKnowledge) -> LearningPlan:
        """Create a learning plan from extracted knowledge."""
        logger.info("Creating learning plan")
        
        plan = LearningPlan(topic=knowledge.concepts[0] if knowledge.concepts else "Unknown")
        
        # Determine required executors
        for api in knowledge.apis:
            executor_name = f"{api['name'].lower().replace(' ', '_')}_executor"
            plan.required_executors.append(executor_name)
        
        # Define new skills
        for pattern in knowledge.workflow_patterns:
            plan.new_skills.append({
                "name": pattern.get("name", "New Skill"),
                "description": f"Skill for {pattern.get('name', 'New Skill')}"
            })
        
        # Create workflow templates
        for pattern in knowledge.workflow_patterns:
            plan.workflow_templates.append(pattern)
        
        # Define integration points
        plan.integration_points = [
            {
                "module": "skills/executors",
                "type": "new_executor",
                "details": f"Add {plan.required_executors[0]} if needed"
            }
        ]
        
        # Estimate complexity (mock)
        plan.estimated_complexity = 2
        
        logger.info(f"Learning plan created for {plan.topic} with complexity {plan.estimated_complexity}")
        return plan


# Module-level singleton
learning_pipeline = LearningPipeline()
