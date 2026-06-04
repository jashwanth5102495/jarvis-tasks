
"""
master_test_runner.py
=====================
Master test runner for JARVIS AI Operating System.
Orchestrates all milestone, integration, stress, and regression tests.
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

# Add the project root to sys.path so we can import all modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from master_testing.milestone_validator import milestone_validator
from master_testing.report_generator import report_generator
from master_testing.regression_guard import regression_guard


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS Master Test Runner - Automated validation for all JARVIS milestones"
    )
    
    parser.add_argument(
        "--all", "--full-system",
        action="store_true",
        help="Run all available milestone tests and generate reports"
    )
    
    parser.add_argument(
        "--milestone", "-m",
        type=int,
        help="Run tests for a single specific milestone (e.g., --milestone 6)"
    )
    
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current test results as the regression baseline"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("[JARVIS AI Operating System] - Master Test Runner")
    print("="*70 + "\n")
    
    # Handle different modes
    if args.milestone:
        print(f"Running tests for Milestone {args.milestone}...")
        results = {args.milestone: milestone_validator.validate_milestone(args.milestone)}
        
        # Generate reports for this single milestone
        report_generator.generate_json_report(results)
        report_generator.generate_markdown_report(results)
        report_generator.generate_html_report(results)
        
    elif args.all:
        print("Running full-system validation...")
        results = milestone_validator.validate_all_milestones()
        
        # Check for regressions
        regression_check = regression_guard.check_for_regressions(results)
        
        # Generate reports
        report_generator.generate_json_report(results)
        report_generator.generate_markdown_report(results)
        report_generator.generate_html_report(results)
        
        if args.save_baseline:
            print("\nSaving current results as regression baseline...")
            regression_guard.save_baseline(results)
        
        # Print final summary
        print("\n" + "="*70)
        print("FINAL TEST SUMMARY")
        print("="*70)
        total_passed = sum(1 for r in results.values() if r.passed)
        total_tested = len(results)
        print(f"Total tested: {total_tested}")
        print(f"Passed:      {total_passed} [OK]")
        print(f"Failed:      {total_tested - total_passed} [FAIL]")
        print(f"Pass rate:   {(total_passed/total_tested*100):.1f}%")
        if regression_check.get("has_regressions"):
            print("\n[WARNING] REGRESSIONS DETECTED - check reports for details!")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
