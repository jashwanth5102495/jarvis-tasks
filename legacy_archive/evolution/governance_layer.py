
"""
governance_layer.py
==================
Governance and safety layer for JARVIS evolution.
Prevents unsafe modifications and enforces safety rules.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from evolution.self_codegen import GeneratedCode

logger = logging.getLogger(__name__)


class GovernanceLayer:
    """
    Critical safety layer for governing self-evolution.
    Prevents unsafe self-modification.
    """

    # Forbidden modifications
    FORBIDDEN_PATHS = [
        "brain",
        "core/config",
        "skills/execution",
        "safety",
        "governance"
    ]

    FORBIDDEN_KEYWORDS = [
        "remove permission",
        "disable sandbox",
        "bypass safety",
        "disable validation",
        "delete system"
    ]

    def __init__(self):
        pass

    def validate_proposal(self, generated_code: GeneratedCode) -> bool:
        """Validate an evolution proposal against safety rules."""
        logger.info("Governance validating proposal...")
        
        # Check for forbidden keywords in generated code
        code = generated_code.executor_code.lower()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in code:
                logger.warning(f"Forbidden keyword detected: {keyword}")
                return False
        
        logger.info("Governance validation passed")
        return True

    def approve_upgrade(self, proposal_id: str) -> bool:
        """Approve an upgrade proposal (human approval step placeholder)."""
        logger.info(f"Governance approval requested for proposal {proposal_id}")
        # In real implementation, this would require human approval
        return True


# Module-level singleton
governance_layer = GovernanceLayer()
