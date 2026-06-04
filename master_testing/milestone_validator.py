
"""
milestone_validator.py
======================
Validator for individual JARVIS milestones.
Runs tests associated with each milestone and collects results.
"""

from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class MilestoneValidationResult:
    milestone: int
    passed: bool = False
    execution_time: float = 0.0
    test_output: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class MilestoneValidator:
    """Validates individual milestones by running their tests."""

    MILESTONE_TEST_MAP = {
        6: "tests/test_llm.py",
        9: "tests/test_evolution.py"
    }

    MILESTONE_NAMES = {
        1: "Brain Foundation",
        2: "Skills Framework",
        3: "Multi-Skill Orchestration",
        4: "Computer Control System",
        5: "Autonomous Agents & Continuous Memory",
        6: "Local LLM Integration",
        7: "Voice & Conversational Intelligence",
        8: "Distributed AI Operating System",
        9: "Self-Evolving AI System"
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def validate_milestone(self, milestone: int) -> MilestoneValidationResult:
        """Validate a single milestone by running its test file."""
        test_file = self.MILESTONE_TEST_MAP.get(milestone)
        if not test_file:
            print(f"Warning: No test file defined for Milestone {milestone}, marking as skipped.")
            return MilestoneValidationResult(
                milestone=milestone,
                passed=False,
                test_output="No test file available for this milestone"
            )
        
        test_path = self.project_root / test_file
        if not test_path.exists():
            print(f"Warning: Test file {test_path} does not exist for Milestone {milestone}.")
            return MilestoneValidationResult(
                milestone=milestone,
                passed=False,
                test_output="Test file not found"
            )
        
        start_time = datetime.now()
        result = MilestoneValidationResult(milestone=milestone)
        
        try:
            print(f"\n--- Validating Milestone {milestone}: {self.MILESTONE_NAMES.get(milestone, 'Unknown')} ---")
            process = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300  # 5 minutes max per test file
            )
            end_time = datetime.now()
            
            result.execution_time = (end_time - start_time).total_seconds()
            result.test_output = process.stdout + "\n" + process.stderr
            result.passed = (process.returncode == 0)
            
            if result.passed:
                print(f"[OK] Milestone {milestone} passed!")
            else:
                print(f"[FAIL] Milestone {milestone} failed!")
                
        except subprocess.TimeoutExpired:
            result.test_output = "Test timed out after 5 minutes"
            result.passed = False
        except Exception as e:
            result.test_output = f"Test exception: {str(e)}"
            result.passed = False
            
        return result

    def validate_all_milestones(self) -> Dict[int, MilestoneValidationResult]:
        """Validate all available milestones."""
        all_results = {}
        for milestone in self.MILESTONE_TEST_MAP:
            all_results[milestone] = self.validate_milestone(milestone)
        return all_results


# Singleton instance (use project root from __file__)
project_root = Path(__file__).parent.parent
milestone_validator = MilestoneValidator(project_root=project_root)
