
"""
regression_guard.py
===================
Regression protection system for JARVIS master testing.
Saves baseline test results and detects regressions.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from master_testing.milestone_validator import MilestoneValidationResult


class RegressionGuard:
    """Protects against regressions by comparing against a baseline."""

    def __init__(self, data_dir: Path):
        self.baseline_file = data_dir / "test_baseline.json"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_baseline(self, test_results: Dict[int, MilestoneValidationResult]):
        """Save current test results as the new baseline."""
        baseline = {
            "timestamp": datetime.now().isoformat(),
            "milestones": {}
        }
        for milestone, result in test_results.items():
            baseline["milestones"][str(milestone)] = {
                "passed": result.passed
            }
        with open(self.baseline_file, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)
        print(f"[OK] Baseline saved to: {self.baseline_file}")

    def check_for_regressions(self, test_results: Dict[int, MilestoneValidationResult]) -> Dict[str, Any]:
        """Compare against baseline and report regressions."""
        if not self.baseline_file.exists():
            print("Warning: No baseline found. Saving current results as new baseline.")
            self.save_baseline(test_results)
            return {"has_regressions": False, "regressions": []}
        
        with open(self.baseline_file, "r", encoding="utf-8") as f:
            baseline = json.load(f)
        
        regressions = []
        for milestone, result in test_results.items():
            baseline_entry = baseline.get("milestones", {}).get(str(milestone))
            if baseline_entry and baseline_entry.get("passed") and not result.passed:
                regressions.append({
                    "milestone": milestone,
                    "message": f"Milestone {milestone} was passing, now failing"
                })
        
        if regressions:
            print("[WARNING] REGRESSIONS DETECTED!")
            for r in regressions:
                print(f"  - {r['message']}")
        else:
            print("[OK] No regressions detected")
        
        return {
            "has_regressions": len(regressions) > 0,
            "regressions": regressions
        }


# Singleton instance
data_dir = Path(__file__).parent.parent / "data"
regression_guard = RegressionGuard(data_dir=data_dir)
