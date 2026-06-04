
"""
Master Testing System for JARVIS AI Operating System.
Provides end-to-end validation, milestone testing, integration, stress, regression, and recovery testing.
"""

from master_testing.master_test_runner import main
from master_testing.milestone_validator import milestone_validator
from master_testing.report_generator import report_generator
from master_testing.regression_guard import regression_guard
from master_testing.test_registry import test_registry

__all__ = [
    "main",
    "milestone_validator",
    "report_generator",
    "regression_guard",
    "test_registry"
]
