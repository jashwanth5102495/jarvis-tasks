
"""
test_registry.py
================
Test registry for JARVIS master testing system.
Tracks all available tests, milestone ownership, dependencies, etc.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class TestEntry:
    test_name: str
    milestone: int
    risk: str  # "SAFE", "LOW", "MEDIUM", "HIGH"
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    required_services: List[str] = field(default_factory=list)


class TestRegistry:
    """Registry for all JARVIS tests."""

    def __init__(self):
        self.registry_file = Path(__file__).parent.parent / "data" / "test_registry.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.tests: Dict[str, TestEntry] = self._load_registry()

    def register_test(self, test_entry: TestEntry):
        """Register a new test."""
        self.tests[test_entry.test_name] = test_entry
        self._save_registry()

    def get_tests_for_milestone(self, milestone: int) -> List[TestEntry]:
        """Get all tests for a specific milestone."""
        return [t for t in self.tests.values() if t.milestone == milestone]

    def get_all_tests(self) -> List[TestEntry]:
        """Get all registered tests."""
        return list(self.tests.values())

    def _load_registry(self) -> Dict[str, TestEntry]:
        """Load registry from disk, or create default registry if not exists."""
        if not self.registry_file.exists():
            return self._create_default_registry()
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                t["test_name"]: TestEntry(**t) for t in data.get("tests", [])
            }
        except Exception as e:
            print(f"Warning: Failed to load test registry: {e}, using default.")
            return self._create_default_registry()

    def _save_registry(self):
        data = {
            "tests": [
                {
                    "test_name": t.test_name,
                    "milestone": t.milestone,
                    "risk": t.risk,
                    "description": t.description,
                    "dependencies": t.dependencies,
                    "required_services": t.required_services
                }
                for t in self.tests.values()
            ]
        }
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _create_default_registry(self) -> Dict[str, TestEntry]:
        """Create a default registry of tests based on existing test files."""
        default_tests = [
            # Milestone 6: LLM
            TestEntry(
                test_name="test_llm",
                milestone=6,
                risk="SAFE",
                description="Tests LLM integration, model registry, token monitoring"
            ),
            # Milestone 7: Voice
            TestEntry(
                test_name="test_voice",
                milestone=7,
                risk="SAFE",
                description="Tests voice system, wake word, TTS, conversation manager"
            ),
            # Milestone 8: Distributed
            TestEntry(
                test_name="test_distributed",
                milestone=8,
                risk="SAFE",
                description="Tests distributed system, node registry, sync, remote execution"
            ),
            # Milestone 9: Evolution
            TestEntry(
                test_name="test_evolution",
                milestone=9,
                risk="SAFE",
                description="Tests self-evolution, research, code gen, validation, governance"
            )
        ]
        registry = {t.test_name: t for t in default_tests}
        self.tests = registry
        self._save_registry()
        return registry


# Module-level singleton
test_registry = TestRegistry()
