
"""
evolution_manager.py
====================
Main manager for JARVIS self-evolution system.
Coordinates research, learning, code generation, validation, and upgrades.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from evolution.research_engine import research_engine
from evolution.knowledge_extractor import knowledge_extractor
from evolution.learning_pipeline import learning_pipeline
from evolution.self_codegen import self_codegen
from evolution.validation_engine import validation_engine
from evolution.sandbox_lab import sandbox_lab
from evolution.skill_registry import skill_registry
from evolution.architecture_optimizer import architecture_optimizer
from evolution.upgrade_manager import upgrade_manager
from evolution.rollback_manager import rollback_manager
from evolution.governance_layer import governance_layer
from evolution.capability_tracker import capability_tracker

logger = logging.getLogger(__name__)


@dataclass
class EvolutionStatus:
    """Current status of the evolution system."""
    is_active: bool = False
    current_session_id: Optional[str] = None
    current_stage: Optional[str] = None
    pending_upgrades: int = 0
    last_evolution: Optional[datetime] = None


class EvolutionManager:
    """
    Main manager orchestrating all self-evolution operations.
    """

    def __init__(self):
        self.status = EvolutionStatus()

    def start_learning_session(self, goal: str) -> Dict[str, Any]:
        """Start a new self-evolution session."""
        logger.info(f"Starting evolution session for goal: {goal}")
        session_id = f"evo_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.status.is_active = True
        self.status.current_session_id = session_id
        self.status.current_stage = "research"

        # Stage 1: Research
        research_results = research_engine.research(goal)

        # Stage 2: Knowledge extraction
        knowledge = knowledge_extractor.extract(research_results)

        # Stage 3: Learning pipeline
        learning_plan = learning_pipeline.create_plan(knowledge)

        # Stage 4: Code generation
        generated_code = self_codegen.generate(learning_plan)

        # Stage 5: Governance check
        if not governance_layer.validate_proposal(generated_code):
            logger.warning("Governance rejected the upgrade proposal")
            return {
                "status": "rejected",
                "reason": "Governance validation failed"
            }

        # Stage 6: Sandbox validation
        validation_result = sandbox_lab.test(generated_code)
        if not validation_result.success:
            logger.warning("Sandbox validation failed")
            return {
                "status": "failed",
                "reason": validation_result.error
            }

        # Stage 7: Full validation
        if not validation_engine.validate(generated_code):
            logger.warning("Full validation failed")
            return {
                "status": "failed",
                "reason": "Validation engine rejected"
            }

        # Stage 8: Upgrade proposal
        proposal = upgrade_manager.create_proposal(generated_code, knowledge)

        self.status.current_stage = "complete"
        self.status.last_evolution = datetime.now()

        logger.info("Evolution session completed successfully")
        return {
            "status": "success",
            "session_id": session_id,
            "proposal": proposal
        }

    def apply_upgrade(self, proposal_id: str) -> Dict[str, Any]:
        """Apply a validated upgrade proposal."""
        logger.info(f"Applying upgrade proposal: {proposal_id}")
        result = upgrade_manager.apply(proposal_id)

        if result["success"]:
            capability_tracker.record_upgrade(result)
        else:
            rollback_manager.rollback(proposal_id)

        return result

    def get_status(self) -> Dict[str, Any]:
        """Get the current evolution system status."""
        return {
            "is_active": self.status.is_active,
            "current_session_id": self.status.current_session_id,
            "current_stage": self.status.current_stage,
            "pending_upgrades": self.status.pending_upgrades,
            "last_evolution": self.status.last_evolution.isoformat() if self.status.last_evolution else None,
            "capabilities": capability_tracker.get_summary()
        }


# Module-level singleton
evolution_manager = EvolutionManager()
